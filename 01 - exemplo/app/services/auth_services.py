import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from app.services.cep_services import DB_PATH

def init_user_db():
    """Inicializa a tabela de usuários no banco de dados SQLite local com suporte a aprovações."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            approved INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    
    # Executar Migrações do SQLite: adiciona as colunas 'approved' e 'is_admin' se elas não existirem
    # (Evita erro operacional em bancos de dados criados anteriormente com esquemas antigos)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN approved INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass # A coluna já existe no banco
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass # A coluna já existe no banco
        
    conn.close()

def seed_admin():
    """
    Garante que a conta do administrador 'vinicius' exista no banco local 
    com as credenciais exatas solicitadas:
    Login: vinicius
    Senha: Vi@250793l
    Status: Aprovado e Administrador.
    """
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    admin_username = "vinicius"
    admin_password = "Vi@250793l"
    
    # Criptografar senha do administrador
    password_hash = generate_password_hash(admin_password)
    
    # Checar se o admin já está registrado
    cursor.execute("SELECT id FROM users WHERE username = ?", (admin_username,))
    row = cursor.fetchone()
    
    if not row:
        # Se não existe, criar a conta
        cursor.execute("""
            INSERT INTO users (username, password_hash, approved, is_admin)
            VALUES (?, ?, 1, 1)
        """, (admin_username, password_hash))
    else:
        # Se já existe, garantir que a senha e privilégios estão atualizados
        cursor.execute("""
            UPDATE users 
            SET password_hash = ?, approved = 1, is_admin = 1 
            WHERE username = ?
        """, (password_hash, admin_username))
        
    conn.commit()
    conn.close()

def criar_usuario(username, password):
    """
    Cadastra um novo usuário no banco de dados como pendente de aprovação (approved = 0).
    Retorna True em caso de sucesso.
    """
    if not username or not password:
        raise ValueError("Usuário e senha são obrigatórios.")
        
    username_cleaned = username.strip().lower()
    
    # Segurança: Impedir criação manual com privilégio admin sob o username "vinicius" fora da rotina do seed
    if username_cleaned == "vinicius":
        raise ValueError("Este nome de usuário é reservado para o administrador.")
        
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    password_hash = generate_password_hash(password)
    
    try:
        # Novas contas iniciam com approved = 0 (Pendente) e is_admin = 0 (Comum)
        cursor.execute("""
            INSERT INTO users (username, password_hash, approved, is_admin) 
            VALUES (?, ?, 0, 0)
        """, (username_cleaned, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        raise ValueError("Este nome de usuário já está sendo utilizado.")
    except Exception as e:
        raise RuntimeError(f"Erro ao cadastrar usuário: {str(e)}")
    finally:
        conn.close()

def verificar_usuario(username, password):
    """
    Valida as credenciais de um usuário.
    Caso válidas, retorna um dicionário com os dados do usuário, incluindo status de aprovação e admin.
    Caso inválidas, retorna None.
    """
    if not username or not password:
        return None
        
    username_cleaned = username.strip().lower()
    
    init_user_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, password_hash, approved, is_admin 
        FROM users 
        WHERE username = ?
    """, (username_cleaned,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        user_id = row[0]
        user_name = row[1]
        password_hash = row[2]
        approved = row[3]
        is_admin = row[4]
        
        if check_password_hash(password_hash, password):
            return {
                "id": user_id,
                "username": user_name,
                "approved": bool(approved),
                "is_admin": bool(is_admin)
            }
            
    return None
