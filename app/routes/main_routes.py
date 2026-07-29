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
from app.services.profile_services import get_user_profile, save_or_update_user_profile
from app.services.taco_services import search_taco_foods, get_taco_food_by_id
from app.services.openfoodfacts_services import fetch_product_by_barcode, search_openfoodfacts_by_name
from app.services.diet_services import (
    get_daily_diet_summary,
    add_user_meal,
    delete_user_meal,
    add_food_to_meal,
    delete_meal_item,
    get_today_date_str
)

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/calculadora', methods=['GET', 'POST'])
@login_required
def calculator():
    user_id = session.get('user_id')
    latest_bmr = get_latest_user_bmr(user_id)
    user_profile = get_user_profile(user_id)
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
        
        save_bmr_record(user_id, gender, weight, height, age, activity_level)
        return redirect(url_for('main.macronutrients'))
        
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
    elif not calculation_result and user_profile:
        weight = user_profile['current_weight']
        height = user_profile['height']
        age = user_profile['age']
        gender = user_profile['gender']
        activity_level = user_profile['activity_level']
        
        bmr, tdee = calculate_bmr_and_tdee(gender, weight, height, age, activity_level)
        calculation_result = {
            'gender': gender,
            'weight': weight,
            'height': height,
            'age': age,
            'activity_level': activity_level,
            'bmr': bmr,
            'tdee': tdee,
            'from_profile': True,
            'targets': {
                'weight_loss_mild': round(tdee - 300, 2),
                'weight_loss_normal': round(tdee - 500, 2),
                'weight_gain_mild': round(tdee + 300, 2),
                'weight_gain_normal': round(tdee + 500, 2)
            }
        }
            
    return render_template('bmr_calculator.html', result=calculation_result, profile=user_profile)


@main.route('/api/save-bmr', methods=['POST'])
@login_required
def api_save_bmr():
    data = request.get_json() or {}
    gender = data.get('gender', 'male')
    weight = float(data.get('weight', 70))
    height = float(data.get('height', 170))
    age = int(data.get('age', 25))
    activity_level = float(data.get('activity_level', 1.2))

    user_id = session.get('user_id')
    bmr, tdee = calculate_bmr_and_tdee(gender, weight, height, age, activity_level)
    save_bmr_record(user_id, gender, weight, height, age, activity_level)

    return jsonify({'success': True, 'bmr': bmr, 'tdee': tdee})


@main.route('/perfil', methods=['GET'])
@login_required
def profile():
    user_id = session.get('user_id')
    user_prof = get_user_profile(user_id)
    return render_template('profile.html', profile=user_prof)


@main.route('/salvar-perfil', methods=['POST'])
@login_required
def save_profile():
    user_id = session.get('user_id')
    full_name = request.form.get('full_name')
    gender = request.form.get('gender')
    age = request.form.get('age')
    height = request.form.get('height')
    current_weight = request.form.get('current_weight')
    goal_type = request.form.get('goal_type')
    target_weight_change_kg = request.form.get('target_weight_change_kg')
    target_timeframe_weeks = request.form.get('target_timeframe_weeks')
    weekly_pace = request.form.get('weekly_pace', 'recommended')
    activity_level = request.form.get('activity_level')

    try:
        save_or_update_user_profile(
            user_id, full_name, gender, age, height, current_weight,
            goal_type, target_weight_change_kg, target_timeframe_weeks, activity_level, weekly_pace
        )
        flash('Perfil e metas salvas com sucesso! Dados sincronizados com a calculadora corporal.', 'success')
        return redirect(url_for('main.calculator'))
    except Exception as e:
        flash(f'Erro ao salvar perfil: {str(e)}', 'danger')

    return redirect(url_for('main.profile'))


@main.route('/macronutrientes', methods=['GET', 'POST'])
@login_required
def macronutrients():
    user_id = session.get('user_id')
    latest_bmr = get_latest_user_bmr(user_id)
    latest_macro = get_latest_user_macro(user_id)

    base_calories = latest_bmr['tdee'] if latest_bmr else 2000.0
    
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
        total_pct = float(carb_pct) + float(protein_pct) + float(fat_pct)
        if abs(total_pct - 100.0) > 0.5:
            flash('A soma das porcentagens dos macronutrientes deve ser igual a 100%.', 'danger')
            return redirect(url_for('main.macronutrients'))

        save_macro_record(user_id, target_calories, carb_pct, protein_pct, fat_pct)
        flash('Divisão de Macronutrientes salva no seu perfil com sucesso! Agora você pode montar sua dieta diária.', 'success')
        return redirect(url_for('main.diet'))
    except Exception as e:
        flash(f'Erro ao salvar macronutrientes: {str(e)}', 'danger')

    return redirect(url_for('main.macronutrients'))


# ================= DIET & MEALS ROUTES =================

@main.route('/dieta', methods=['GET'])
@login_required
def diet():
    user_id = session.get('user_id')
    meal_date = request.args.get('date', get_today_date_str())
    
    diet_data = get_daily_diet_summary(user_id, meal_date)
    return render_template('diet.html', diet=diet_data, current_date=meal_date)


@main.route('/dieta/adicionar-refeicao', methods=['POST'])
@login_required
def add_meal():
    user_id = session.get('user_id')
    meal_name = request.form.get('meal_name', '').strip()
    meal_date = request.form.get('meal_date', get_today_date_str())
    
    success, result = add_user_meal(user_id, meal_name, meal_date)
    if success:
        flash(f'Refeição "{meal_name}" adicionada com sucesso!', 'success')
    else:
        flash(result, 'danger')
        
    return redirect(url_for('main.diet', date=meal_date))


@main.route('/dieta/remover-refeicao/<int:meal_id>', methods=['POST'])
@login_required
def remove_meal(meal_id):
    user_id = session.get('user_id')
    meal_date = request.form.get('meal_date', get_today_date_str())
    
    if delete_user_meal(user_id, meal_id):
        flash('Refeição removida da dieta.', 'success')
    else:
        flash('Não foi possível remover a refeição.', 'danger')
        
    return redirect(url_for('main.diet', date=meal_date))


@main.route('/dieta/adicionar-alimento', methods=['POST'])
@login_required
def add_food():
    meal_id = request.form.get('meal_id')
    meal_date = request.form.get('meal_date', get_today_date_str())
    food_source = request.form.get('food_source', 'taco')
    taco_food_id = request.form.get('taco_food_id')
    amount_g = request.form.get('amount_g', 100)
    unit_name = request.form.get('unit_name', 'g')
    unit_qty = request.form.get('unit_qty', 0)

    # Custom food or Barcode fields
    custom_name = request.form.get('custom_name', '').strip()
    custom_kcal = request.form.get('custom_kcal', 0)
    custom_p = request.form.get('custom_p', 0)
    custom_c = request.form.get('custom_c', 0)
    custom_f = request.form.get('custom_f', 0)

    try:
        if food_source in ['custom', 'barcode']:
            if not custom_name:
                flash('Informe o nome do alimento ou produto.', 'danger')
                return redirect(url_for('main.diet', date=meal_date))
                
            success, result = add_food_to_meal(
                meal_id,
                taco_food_id=None,
                amount_g=amount_g,
                custom_name=custom_name,
                custom_kcal=custom_kcal,
                custom_p=custom_p,
                custom_c=custom_c,
                custom_f=custom_f,
                unit_name=unit_name,
                unit_qty=unit_qty
            )
        else:
            taco_id = int(taco_food_id) if taco_food_id and taco_food_id.isdigit() else None
            if not taco_id:
                flash('Selecione um alimento da lista.', 'warning')
                return redirect(url_for('main.diet', date=meal_date))
                
            success, result = add_food_to_meal(
                meal_id,
                taco_id,
                amount_g,
                unit_name=unit_name,
                unit_qty=unit_qty
            )

        if success:
            flash('Alimento adicionado à refeição!', 'success')
        else:
            flash(result, 'danger')
    except Exception as e:
        flash(f'Erro ao registrar alimento: {str(e)}', 'danger')

    return redirect(url_for('main.diet', date=meal_date))


@main.route('/dieta/remover-item/<int:item_id>', methods=['POST'])
@login_required
def remove_food_item(item_id):
    user_id = session.get('user_id')
    meal_date = request.args.get('date', get_today_date_str())

    if delete_meal_item(user_id, item_id):
        flash('Alimento removido da refeição.', 'success')
    else:
        flash('Erro ao remover alimento.', 'danger')

    return redirect(url_for('main.diet', date=meal_date))


@main.route('/api/taco/search', methods=['GET'])
@login_required
def api_taco_search():
    query = request.args.get('q', '')
    foods = search_taco_foods(query)
    return jsonify({'success': True, 'foods': foods})


@main.route('/api/barcode/search', methods=['GET'])
@login_required
def api_barcode_search():
    code = request.args.get('code', '').strip()
    result = fetch_product_by_barcode(code)
    return jsonify(result)


@main.route('/api/openfoodfacts/search', methods=['GET'])
@login_required
def api_off_search():
    query = request.args.get('q', '').strip()
    foods = search_openfoodfacts_by_name(query)
    return jsonify({'success': True, 'foods': foods})
