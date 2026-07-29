from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db

def create_user(username, email, password):
    """Cadastra um novo usuário no banco de dados com senha criptografada."""
    db = get_db()
    cursor = db.cursor()

    username = username.strip()
    email = email.strip().lower()

    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
    if cursor.fetchone():
        return False, "Nome de usuário ou e-mail já cadastrado."

    password_hash = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, 0)",
        (username, email, password_hash)
    )
    db.commit()

    return True, "Usuário cadastrado com sucesso!"

def authenticate_user(identifier, password):
    """Autentica o usuário por username ou email e valida o hash da senha."""
    db = get_db()
    cursor = db.cursor()

    identifier = identifier.strip()

    cursor.execute(
        "SELECT id, username, email, password_hash, is_admin FROM users WHERE username = ? OR email = ?",
        (identifier, identifier.lower())
    )
    user = cursor.fetchone()

    if not user:
        return False, "Usuário ou e-mail não encontrado."

    if not check_password_hash(user['password_hash'], password):
        return False, "Senha incorreta."

    return True, {
        'id': user['id'],
        'username': user['username'],
        'email': user['email'],
        'is_admin': bool(user['is_admin'])
    }
