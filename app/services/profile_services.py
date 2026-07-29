from app.database import get_db

GOAL_LABELS = {
    'weight_loss': 'Emagrecimento / Perda de Gordura',
    'weight_gain': 'Ganho de Peso / Massa Muscular',
    'maintenance': 'Manutenção de Peso'
}

def get_user_profile(user_id):
    """Retorna o perfil do usuário cadastrado no banco."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, user_id, full_name, gender, age, height, current_weight,
               goal_type, target_weight_change_kg, target_timeframe_weeks,
               activity_level, created_at, updated_at
        FROM user_profiles
        WHERE user_id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    if not row:
        return None
    
    profile = dict(row)
    profile['goal_label'] = GOAL_LABELS.get(profile['goal_type'], 'Manutenção de Peso')
    
    # Calculate weekly target rate
    weeks = profile.get('target_timeframe_weeks') or 1
    change_kg = profile.get('target_weight_change_kg') or 0.0
    profile['weekly_rate_kg'] = round(change_kg / max(weeks, 1), 2)
    return profile

def save_or_update_user_profile(user_id, full_name, gender, age, height, current_weight, goal_type, target_weight_change_kg, target_timeframe_weeks, activity_level):
    """Cria ou atualiza o perfil e metas do usuário."""
    db = get_db()
    cursor = db.cursor()

    full_name = str(full_name or '').strip()
    gender = str(gender or 'male').strip()
    age = int(age or 25)
    height = float(height or 170.0)
    current_weight = float(current_weight or 70.0)
    goal_type = str(goal_type or 'weight_loss').strip()
    target_weight_change_kg = float(target_weight_change_kg or 0.0)
    target_timeframe_weeks = int(target_timeframe_weeks or 8)
    activity_level = float(activity_level or 1.2)

    cursor.execute('SELECT id FROM user_profiles WHERE user_id = ?', (user_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE user_profiles
            SET full_name = ?,
                gender = ?,
                age = ?,
                height = ?,
                current_weight = ?,
                goal_type = ?,
                target_weight_change_kg = ?,
                target_timeframe_weeks = ?,
                activity_level = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (full_name, gender, age, height, current_weight, goal_type, target_weight_change_kg, target_timeframe_weeks, activity_level, user_id))
    else:
        cursor.execute('''
            INSERT INTO user_profiles
            (user_id, full_name, gender, age, height, current_weight, goal_type, target_weight_change_kg, target_timeframe_weeks, activity_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, full_name, gender, age, height, current_weight, goal_type, target_weight_change_kg, target_timeframe_weeks, activity_level))

    db.commit()
    return True
