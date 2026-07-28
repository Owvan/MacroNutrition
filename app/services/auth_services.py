import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db

def create_user(username, email, password):
    username = username.strip()
    email = email.strip().lower()
    
    if not username or not email or not password:
        return False, "Todos os campos são obrigatórios."
    
    if len(password) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres."
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if username or email already exists
    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
    if cursor.fetchone():
        return False, "Nome de usuário ou e-mail já cadastrado."
    
    hashed_password = generate_password_hash(password)
    
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        db.commit()
        return True, "Usuário cadastrado com sucesso! Faça login."
    except sqlite3.IntegrityError:
        return False, "Erro ao cadastrar usuário. Tente novamente."

def authenticate_user(identifier, password):
    identifier = identifier.strip()
    db = get_db()
    cursor = db.cursor()
    
    # Check by username or email
    cursor.execute(
        "SELECT id, username, email, password_hash FROM users WHERE username = ? OR email = ?",
        (identifier, identifier.lower())
    )
    user = cursor.fetchone()
    
    if user and check_password_hash(user['password_hash'], password):
        return True, dict(user)
    
    return False, "Usuário ou senha incorretos."

def get_user_by_id(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, email, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    return dict(user) if user else None
