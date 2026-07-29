from werkzeug.security import generate_password_hash
from app.database import get_db

def list_all_users():
    """Retorna todos os usuários cadastrados com estatísticas de perfil e diário alimentar."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        SELECT u.id, u.username, u.email, u.is_admin, u.created_at,
               p.full_name, p.current_weight, p.goal_type,
               (SELECT COUNT(*) FROM user_meals m WHERE m.user_id = u.id) as meals_count
        FROM users u
        LEFT JOIN user_profiles p ON p.user_id = u.id
        ORDER BY u.id ASC
    ''')
    rows = cursor.fetchall()
    users = []
    for row in rows:
        user_dict = dict(row)
        user_dict['is_admin'] = bool(user_dict['is_admin'])
        user_dict['has_profile'] = bool(user_dict['full_name'])
        users.append(user_dict)
    return users

def toggle_user_admin(user_id, current_admin_id):
    """Alterna os privilégios de administrador de um usuário."""
    if int(user_id) == int(current_admin_id):
        return False, "Você não pode alterar seus próprios privilégios de administrador."

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_admin, username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        return False, "Usuário não localizado."

    new_status = 0 if user['is_admin'] else 1
    cursor.execute("UPDATE users SET is_admin = ? WHERE id = ?", (new_status, user_id))
    db.commit()

    status_label = "Administrador" if new_status else "Usuário Comum"
    return True, f"Privilégios do usuário '{user['username']}' alterados para {status_label}."

def reset_user_password(user_id, new_password):
    """Redefine a senha de um usuário."""
    if not new_password or len(new_password.strip()) < 6:
        return False, "A nova senha deve possuir pelo menos 6 caracteres."

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        return False, "Usuário não localizado."

    pwd_hash = generate_password_hash(new_password.strip())
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, user_id))
    db.commit()

    return True, f"Senha do usuário '{user['username']}' redefinida com sucesso!"

def delete_user_account(user_id, current_admin_id):
    """Exclui a conta de um usuário do sistema."""
    if int(user_id) == int(current_admin_id):
        return False, "Você não pode excluir sua própria conta de administrador."

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        return False, "Usuário não localizado."

    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()

    return True, f"Conta do usuário '{user['username']}' excluída com sucesso!"
