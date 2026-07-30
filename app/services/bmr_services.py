from app.database import get_db, parse_float

ACTIVITY_LABELS = {
    1.2: "Sedentário (pouco ou nenhum exercício)",
    1.375: "Levemente Ativo (exercício leve 1-3 dias/semana)",
    1.55: "Moderadamente Ativo (exercício moderado 3-5 dias/semana)",
    1.725: "Altamente Ativo (exercício pesado 6-7 dias/semana)",
    1.9: "Extremamente Ativo (trabalho braçal ou treino 2x/dia)"
}

def calculate_bmr_and_tdee(gender, weight, height, age, activity_level):
    weight = parse_float(weight, 70.0)
    height = parse_float(height, 170.0)
    age = int(parse_float(age, 25))
    activity_level = parse_float(activity_level, 1.2)
    
    if gender.lower() in ['female', 'feminino']:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        
    tdee = bmr * activity_level
    
    return round(bmr, 2), round(tdee, 2)

def save_bmr_record(user_id, gender, weight, height, age, activity_level):
    bmr, tdee = calculate_bmr_and_tdee(gender, weight, height, age, activity_level)
    activity_label = ACTIVITY_LABELS.get(float(activity_level), "Personalizado")
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO bmr_records 
        (user_id, gender, weight, height, age, activity_level, activity_label, bmr, tdee)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, gender, weight, height, age, activity_level, activity_label, bmr, tdee))
    
    db.commit()
    return cursor.lastrowid

def get_latest_user_bmr(user_id):
    """Busca o cálculo mais recente de TMB e TDEE do usuário."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, gender, weight, height, age, activity_level, activity_label, bmr, tdee, created_at
        FROM bmr_records
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    ''', (user_id,))
    record = cursor.fetchone()
    return dict(record) if record else None
