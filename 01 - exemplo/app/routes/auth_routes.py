import sqlite3
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_services import criar_usuario, verificar_usuario
from app.services.cep_services import DB_PATH

auth = Blueprint("auth", __name__)

def login_required(f):
    """
    Decorador para proteger rotas que exigem autenticação.
    Redireciona usuários deslogados para a página de login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Por favor, faça login para acessar esta página.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorador de segurança estrita para proteger rotas administrativas.
    Impede que usuários comuns acessem painéis ou invoquem ações administrativas (escalonamento de privilégios).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Acesso restrito. Por favor, faça login.", "warning")
            return redirect(url_for("auth.login"))
        # Verifica explicitamente se a flag is_admin está ativa na sessão assinada
        if not session.get("is_admin"):
            flash("Acesso negado: Esta operação requer privilégios de administrador.", "danger")
            return redirect(url_for("main.home"))
        return f(*args, **kwargs)
    return decorated_function

@auth.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("main.home"))
        
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not username or not password:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template("register.html")
            
        if len(password) < 6:
            flash("A senha deve conter no mínimo 6 caracteres.", "danger")
            return render_template("register.html")
            
        if password != confirm_password:
            flash("As senhas informadas não coincidem.", "danger")
            return render_template("register.html")
            
        try:
            # Cadastra o usuário como pendente (approved = 0)
            criar_usuario(username, password)
            
            # NÃO faz login automático. Informa a pendência e redireciona ao login.
            flash("Sua conta foi criada com sucesso! Ela está aguardando aprovação por um administrador para que você possa logar.", "info")
            return redirect(url_for("auth.login"))
            
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"Ocorreu um erro ao criar a conta: {str(e)}", "danger")
            
    return render_template("register.html")

@auth.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.home"))
        
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            flash("Preencha o usuário e a senha.", "danger")
            return render_template("login.html")
            
        user = verificar_usuario(username, password)
        
        if user:
            # Segurança: Bloquear login de contas não aprovadas
            if not user["approved"]:
                flash("Sua conta ainda não foi aprovada pelo administrador. Por favor, aguarde a liberação.", "warning")
                return render_template("login.html")
                
            # Salvar dados de autenticação e escopo de privilégios na sessão assinada
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = user["is_admin"]
            
            flash(f"Bem-vindo(a) de volta, {user['username']}!", "success")
            return redirect(url_for("main.home"))
        else:
            flash("Usuário ou senha incorretos.", "danger")
            
    return render_template("login.html")

@auth.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("auth.login"))

# --- ROTAS ADMINISTRATIVAS PROTEGIDAS ---

@auth.route("/admin", methods=["GET"])
@admin_required
def admin_manager():
    """Painel de controle para o administrador aprovar ou excluir contas."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Listar todos os usuários do sistema exceto o próprio administrador master 'vinicius'
    cursor.execute("""
        SELECT id, username, approved, is_admin, created_at 
        FROM users 
        WHERE username != 'vinicius' 
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    users_list = []
    for r in rows:
        users_list.append({
            "id": r[0],
            "username": r[1],
            "approved": bool(r[2]),
            "is_admin": bool(r[3]),
            "created_at": r[4]
        })
        
    return render_template("admin.html", users=users_list)

@auth.route("/admin/aprovar/<int:user_id>", methods=["POST"])
@admin_required
def aprovar_usuario(user_id):
    """Aprova a conta de um usuário pendente."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Parâmetro parametrizado contra SQL Injection
        cursor.execute("UPDATE users SET approved = 1 WHERE id = ?", (user_id,))
        conn.commit()
        
        # Obter nome do usuário para feedback amigável
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        username = row[0] if row else f"ID {user_id}"
        conn.close()
        
        flash(f"Conta de '{username}' aprovada com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao aprovar usuário: {str(e)}", "danger")
        
    return redirect(url_for("auth.admin_manager"))

@auth.route("/admin/deletar/<int:user_id>", methods=["POST"])
@admin_required
def deletar_usuario(user_id):
    """Exclui a conta de um usuário do sistema (comum ou admin)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Segurança Extra: Garantir que não está deletando a conta master 'vinicius'
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row and row[0] == "vinicius":
            conn.close()
            flash("Operação Proibida: Não é possível deletar a conta master do administrador.", "danger")
            return redirect(url_for("auth.admin_manager"))
            
        username = row[0] if row else f"ID {user_id}"
        
        # Deletar registro do usuário de forma parametrizada
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        flash(f"Conta do usuário '{username}' foi excluída permanentemente.", "success")
    except Exception as e:
        flash(f"Erro ao excluir usuário: {str(e)}", "danger")
        
    return redirect(url_for("auth.admin_manager"))

@auth.route("/admin/toggle-admin/<int:user_id>", methods=["POST"])
@admin_required
def alterar_cargo_usuario(user_id):
    """Alterna os privilégios administrativos de um usuário (de comum para adm e vice-versa)."""
    try:
        # Segurança: Impedir alterar os próprios privilégios
        if user_id == session.get("user_id"):
            flash("Você não pode alterar os seus próprios privilégios administrativos.", "danger")
            return redirect(url_for("auth.admin_manager"))
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar o usuário no banco
        cursor.execute("SELECT username, is_admin FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            flash("Usuário não encontrado.", "danger")
            return redirect(url_for("auth.admin_manager"))
            
        username, is_admin = row
        
        # Segurança Extra: Impedir alterar a conta master 'vinicius'
        if username.lower() == "vinicius":
            conn.close()
            flash("Não é possível alterar os privilégios da conta administrativa master.", "danger")
            return redirect(url_for("auth.admin_manager"))
            
        # Inverter privilégio
        novo_is_admin = 0 if is_admin else 1
        cursor.execute("UPDATE users SET is_admin = ? WHERE id = ?", (novo_is_admin, user_id))
        conn.commit()
        conn.close()
        
        cargo = "Administrador" if novo_is_admin else "Usuário Comum"
        flash(f"Privilégios de '{username}' alterados com sucesso para {cargo}!", "success")
    except Exception as e:
        flash(f"Erro ao alterar privilégios: {str(e)}", "danger")
        
    return redirect(url_for("auth.admin_manager"))
