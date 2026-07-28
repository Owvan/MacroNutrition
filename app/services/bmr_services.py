from app.database import get_db

ACTIVITY_LABELS = {
    1.2: "Sedentário (pouco ou nenhum exercício)",
    1.375: "Levemente Ativo (exercício leve 1-3 dias/semana)",
    1.55: "Moderadamente Ativo (exercício moderado 3-5 dias/semana)",
    1.725: "Altamente Ativo (exercício pesado 6-7 dias/semana)",
    1.9: "Extremamente Ativo (trabalho braçal ou treino 2x/dia)"
}

def calculate_bmr_and_tdee(gender, weight, height, age, activity_level):
    weight = float(weight)
    height = float(height)
    age = int(age)
    activity_level = float(activity_level)
    
    if gender.lower() == 'female' or gender.lower() == 'feminino':
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

def get_user_bmr_records(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, gender, weight, height, age, activity_level, activity_label, bmr, tdee, created_at
        FROM bmr_records
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    records = cursor.fetchall()
    return [dict(row) for row in records]

def delete_bmr_record(user_id, record_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM bmr_records WHERE id = ? AND user_id = ?', (record_id, user_id))
    db.commit()
    return cursor.rowcount > 0
