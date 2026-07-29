from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.routes.auth_routes import login_required, admin_required
from app.services.admin_services import (
    list_all_users,
    toggle_user_admin,
    reset_user_password,
    delete_user_account
)

admin = Blueprint('admin', __name__)

@admin.route('/admin/usuarios', methods=['GET'])
@login_required
@admin_required
def manage_users():
    users = list_all_users()
    return render_template('admin_users.html', users=users)

@admin.route('/admin/usuarios/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    current_admin_id = session.get('user_id')
    success, message = toggle_user_admin(user_id, current_admin_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('admin.manage_users'))

@admin.route('/admin/usuarios/reset-senha/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    new_password = request.form.get('new_password')
    success, message = reset_user_password(user_id, new_password)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('admin.manage_users'))

@admin.route('/admin/usuarios/excluir/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    current_admin_id = session.get('user_id')
    success, message = delete_user_account(user_id, current_admin_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('admin.manage_users'))
