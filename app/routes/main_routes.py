from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.routes.auth_routes import login_required
from app.services.bmr_services import (
    calculate_bmr_and_tdee,
    save_bmr_record,
    get_user_bmr_records,
    delete_bmr_record
)

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/calculadora', methods=['GET', 'POST'])
@login_required
def calculator():
    calculation_result = None
    
    if request.method == 'POST':
        gender = request.form.get('gender', 'male')
        weight = float(request.form.get('weight', 70))
        height = float(request.form.get('height', 170))
        age = int(request.form.get('age', 25))
        activity_level = float(request.form.get('activity_level', 1.2))
        should_save = request.form.get('save_record') == 'true'
        
        bmr, tdee = calculate_bmr_and_tdee(gender, weight, height, age, activity_level)
        
        # Additional caloric target suggestions
        targets = {
            'weight_loss_mild': round(tdee - 300, 2),
            'weight_loss_normal': round(tdee - 500, 2),
            'weight_gain_mild': round(tdee + 300, 2),
            'weight_gain_normal': round(tdee + 500, 2)
        }
        
        calculation_result = {
            'gender': gender,
            'weight': weight,
            'height': height,
            'age': age,
            'activity_level': activity_level,
            'bmr': bmr,
            'tdee': tdee,
            'targets': targets
        }
        
        if should_save:
            save_bmr_record(session['user_id'], gender, weight, height, age, activity_level)
            flash('Cálculo salvo no seu histórico com sucesso!', 'success')
            return redirect(url_for('main.history'))
            
    return render_template('bmr_calculator.html', result=calculation_result)

@main.route('/api/calculate-bmr', methods=['POST'])
@login_required
def api_calculate_bmr():
    data = request.get_json() or {}
    gender = data.get('gender', 'male')
    weight = data.get('weight', 70)
    height = data.get('height', 170)
    age = data.get('age', 25)
    activity_level = data.get('activity_level', 1.2)
    
    try:
        bmr, tdee = calculate_bmr_and_tdee(gender, weight, height, age, activity_level)
        targets = {
            'weight_loss_mild': round(tdee - 300, 2),
            'weight_loss_normal': round(tdee - 500, 2),
            'weight_gain_mild': round(tdee + 300, 2),
            'weight_gain_normal': round(tdee + 500, 2)
        }
        return jsonify({
            'success': True,
            'bmr': bmr,
            'tdee': tdee,
            'targets': targets
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@main.route('/historico')
@login_required
def history():
    user_id = session.get('user_id')
    records = get_user_bmr_records(user_id)
    return render_template('history.html', records=records)

@main.route('/deletar-bmr/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    user_id = session.get('user_id')
    if delete_bmr_record(user_id, record_id):
        flash('Registro removido do histórico.', 'success')
    else:
        flash('Não foi possível remover o registro.', 'danger')
    return redirect(url_for('main.history'))
