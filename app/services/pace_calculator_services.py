import math

def calculate_pace_and_deficit(gender, weight, height, age, activity_level, goal_type, weekly_rate_kg):
    """
    Calcula TMB (Mifflin-St Jeor), TDEE, o déficit calórico diário proporcional
    ao ritmo semanal (kg/semana) e aplica as travas de segurança fisiológicas da OMS.
    
    1 kg de gordura corporal ~ 7.700 kcal -> 7.700 / 7 dias = 1.100 kcal/dia por kg/sem.
    """
    height_m = float(height or 170.0) / 100.0
    weight_kg = float(weight or 70.0)
    age = int(age or 25)
    activity_level = float(activity_level or 1.2)
    weekly_rate_kg = float(weekly_rate_kg or 0.50)
    gender = str(gender or 'male').strip().lower()

    if height_m <= 0 or weight_kg <= 0 or age <= 0:
        return None

    # 1. TMB (Mifflin-St Jeor) & Mínimo Vital Fisiológico
    if gender == 'female':
        bmr = (10.0 * weight_kg) + (6.25 * (height_m * 100.0)) - (5.0 * age) - 161.0
        min_safety = max(bmr, 1200.0)
    else:
        bmr = (10.0 * weight_kg) + (6.25 * (height_m * 100.0)) - (5.0 * age) + 5.0
        min_safety = max(bmr, 1500.0)

    # 2. TDEE (Gasto Energético Total Diário)
    tdee = bmr * activity_level

    # 3. Definição do Déficit / Superávit Calórico Efetivo
    is_safe = True
    safe_max_rate = weekly_rate_kg
    warning_msg = None

    if goal_type == 'weight_loss':
        daily_deficit = round(weekly_rate_kg * 1100.0, 1)
        raw_target_calories = tdee - daily_deficit
        
        if raw_target_calories < min_safety:
            is_safe = False
            target_calories = round(min_safety, 1)
            safe_max_rate = round(max(0.1, (tdee - min_safety) / 1100.0), 2)
            daily_deficit = round(tdee - target_calories, 1)
            warning_msg = f"Atenção: A meta foi ajustada para o piso mínimo de segurança fisiológica ({int(min_safety)} kcal/dia) para proteger seu metabolismo. O ritmo máximo recomendado é de {safe_max_rate} kg/semana."
        else:
            target_calories = round(raw_target_calories, 1)

    elif goal_type == 'weight_gain':
        daily_deficit = -round(weekly_rate_kg * 800.0, 1) # Superávit calórico
        target_calories = round(tdee + abs(daily_deficit), 1)
    else: # maintenance
        daily_deficit = 0.0
        target_calories = round(tdee, 1)

    return {
        'bmr': round(bmr, 1),
        'tdee': round(tdee, 1),
        'daily_deficit_kcal': daily_deficit,
        'target_calories': target_calories,
        'min_safety_kcal': round(min_safety, 1),
        'is_safe': is_safe,
        'safe_max_rate_kg': safe_max_rate,
        'warning_msg': warning_msg
    }
