from app.database import get_db

OMS_PRESET = {
    'name': 'Recomendação OMS (Equilibrada)',
    'carb_pct': 50.0,
    'protein_pct': 20.0,
    'fat_pct': 30.0
}

PRESETS = {
    'oms': OMS_PRESET,
    'sports': {'name': 'Ganho de Massa / Esportiva', 'carb_pct': 40.0, 'protein_pct': 30.0, 'fat_pct': 30.0},
    'lowcarb': {'name': 'Low Carb', 'carb_pct': 25.0, 'protein_pct': 40.0, 'fat_pct': 35.0},
    'keto': {'name': 'Cetogênica', 'carb_pct': 5.0, 'protein_pct': 25.0, 'fat_pct': 70.0}
}

def calculate_macros(target_calories, carb_pct, protein_pct, fat_pct):
    target_calories = float(target_calories)
    carb_pct = float(carb_pct)
    protein_pct = float(protein_pct)
    fat_pct = float(fat_pct)

    carb_kcal = target_calories * (carb_pct / 100.0)
    protein_kcal = target_calories * (protein_pct / 100.0)
    fat_kcal = target_calories * (fat_pct / 100.0)

    carb_g = round(carb_kcal / 4.0, 1)
    protein_g = round(protein_kcal / 4.0, 1)
    fat_g = round(fat_kcal / 9.0, 1)

    return {
        'target_calories': target_calories,
        'carb_pct': carb_pct,
        'protein_pct': protein_pct,
        'fat_pct': fat_pct,
        'carb_kcal': round(carb_kcal, 1),
        'protein_kcal': round(protein_kcal, 1),
        'fat_kcal': round(fat_kcal, 1),
        'carb_g': carb_g,
        'protein_g': protein_g,
        'fat_g': fat_g
    }

def save_macro_record(user_id, target_calories, carb_pct, protein_pct, fat_pct):
    res = calculate_macros(target_calories, carb_pct, protein_pct, fat_pct)
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO macro_records 
        (user_id, target_calories, carb_pct, protein_pct, fat_pct, carb_g, protein_g, fat_g)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        res['target_calories'],
        res['carb_pct'],
        res['protein_pct'],
        res['fat_pct'],
        res['carb_g'],
        res['protein_g'],
        res['fat_g']
    ))
    db.commit()
    return cursor.lastrowid

def get_latest_user_macro(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, target_calories, carb_pct, protein_pct, fat_pct, carb_g, protein_g, fat_g, created_at
        FROM macro_records
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    ''', (user_id,))
    row = cursor.fetchone()
    return dict(row) if row else None
