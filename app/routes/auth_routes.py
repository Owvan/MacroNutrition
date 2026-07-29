from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_services import create_user, authenticate_user

auth = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id') or not session.get('is_admin'):
            flash('Acesso negado. Esta área é restrita a administradores do sistema.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        
        success, result = authenticate_user(identifier, password)
        if success:
            session.clear()
            session['user_id'] = result['id']
            session['username'] = result['username']
            session['email'] = result['email']
            session['is_admin'] = result['is_admin']
            flash(f'Bem-vindo de volta, {result["username"]}!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(result, 'danger')
            
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('register.html', username=username, email=email)
            
        success, message = create_user(username, email, password)
        if success:
            flash(message, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'danger')
            
    return render_template('register.html')

@auth.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta com segurança.', 'info')
    return redirect(url_for('auth.login'))
