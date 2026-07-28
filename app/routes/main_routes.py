from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.routes.auth_routes import login_required
from app.services.bmr_services import calculate_bmr_and_tdee, save_bmr_record, get_latest_user_bmr
from app.services.macro_services import (
    calculate_macros,
    save_macro_record,
    get_latest_user_macro,
    PRESETS,
    OMS_PRESET
)

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/calculadora', methods=['GET', 'POST'])
@login_required
def calculator():
    user_id = session.get('user_id')
    latest_bmr = get_latest_user_bmr(user_id)
    calculation_result = None

    if request.method == 'POST':
        gender = request.form.get('gender', 'male')
        weight = float(request.form.get('weight', 70))
        height = float(request.form.get('height', 170))
        age = int(request.form.get('age', 25))
        activity_level = float(request.form.get('activity_level', 1.2))
        
        bmr, tdee = calculate_bmr_and_tdee(gender, weight, height, age, activity_level)
        
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
        
        # Save BMR calculation to database
        save_bmr_record(user_id, gender, weight, height, age, activity_level)
        flash('Cálculo corporal salvo com sucesso! Agora defina a divisão dos seus macronutrientes abaixo.', 'success')
        return redirect(url_for('main.macronutrients'))
        
    # If GET request and user has a previous record, load it into result
    if not calculation_result and latest_bmr:
        tdee = latest_bmr['tdee']
        calculation_result = {
            'gender': latest_bmr['gender'],
            'weight': latest_bmr['weight'],
            'height': latest_bmr['height'],
            'age': latest_bmr['age'],
            'activity_level': latest_bmr['activity_level'],
            'bmr': latest_bmr['bmr'],
            'tdee': tdee,
            'targets': {
                'weight_loss_mild': round(tdee - 300, 2),
                'weight_loss_normal': round(tdee - 500, 2),
                'weight_gain_mild': round(tdee + 300, 2),
                'weight_gain_normal': round(tdee + 500, 2)
            }
        }
            
    return render_template('bmr_calculator.html', result=calculation_result)


@main.route('/macronutrientes', methods=['GET', 'POST'])
@login_required
def macronutrients():
    user_id = session.get('user_id')
    latest_bmr = get_latest_user_bmr(user_id)
    latest_macro = get_latest_user_macro(user_id)

    # Base target calories from latest TDEE or default to 2000 kcal
    base_calories = latest_bmr['tdee'] if latest_bmr else 2000.0
    
    # Preset selections or latest user saved macros
    current_carb_pct = latest_macro['carb_pct'] if latest_macro else OMS_PRESET['carb_pct']
    current_protein_pct = latest_macro['protein_pct'] if latest_macro else OMS_PRESET['protein_pct']
    current_fat_pct = latest_macro['fat_pct'] if latest_macro else OMS_PRESET['fat_pct']
    current_target_cal = latest_macro['target_calories'] if latest_macro else base_calories

    macro_calc = calculate_macros(current_target_cal, current_carb_pct, current_protein_pct, current_fat_pct)

    return render_template(
        'macros.html',
        latest_bmr=latest_bmr,
        base_calories=base_calories,
        macro_calc=macro_calc,
        presets=PRESETS
    )


@main.route('/salvar-macros', methods=['POST'])
@login_required
def save_macros():
    user_id = session.get('user_id')
    target_calories = request.form.get('target_calories', 2000)
    carb_pct = request.form.get('carb_pct', 50)
    protein_pct = request.form.get('protein_pct', 20)
    fat_pct = request.form.get('fat_pct', 30)

    try:
        # Validate total percentage equals 100
        total_pct = float(carb_pct) + float(protein_pct) + float(fat_pct)
        if abs(total_pct - 100.0) > 0.5:
            flash('A soma das porcentagens dos macronutrientes deve ser igual a 100%.', 'danger')
            return redirect(url_for('main.macronutrients'))

        save_macro_record(user_id, target_calories, carb_pct, protein_pct, fat_pct)
        flash('Divisão de Macronutrientes salva no seu perfil com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao salvar macronutrientes: {str(e)}', 'danger')

    return redirect(url_for('main.macronutrients'))


@main.route('/api/calculate-macros', methods=['POST'])
@login_required
def api_calculate_macros():
    data = request.get_json() or {}
    target_calories = data.get('target_calories', 2000)
    carb_pct = data.get('carb_pct', 50)
    protein_pct = data.get('protein_pct', 20)
    fat_pct = data.get('fat_pct', 30)

    try:
        res = calculate_macros(target_calories, carb_pct, protein_pct, fat_pct)
        return jsonify({'success': True, 'data': res})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
