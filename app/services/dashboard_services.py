import datetime
from app.database import get_db
from app.services.profile_services import get_user_profile
from app.services.diet_services import (
    get_daily_diet_summary,
    get_today_date_str,
    get_caloric_history,
    get_caloric_streak
)

def add_weight_entry(user_id, weight, date_str=None, notes=None):
    """Registra uma medição de peso no histórico e atualiza o peso atual no perfil."""
    db = get_db()
    cursor = db.cursor()

    if not date_str:
        date_str = get_today_date_str()

    weight = float(weight)
    notes = str(notes or '').strip()

    # Insert or update entry for user_id on recorded_date
    cursor.execute('''
        SELECT id FROM weight_history
        WHERE user_id = ? AND recorded_date = ?
    ''', (user_id, date_str))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE weight_history
            SET weight = ?, notes = ?, created_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (weight, notes, existing['id']))
    else:
        cursor.execute('''
            INSERT INTO weight_history (user_id, weight, recorded_date, notes)
            VALUES (?, ?, ?, ?)
        ''', (user_id, weight, date_str, notes))

    sync_latest_profile_weight(cursor, user_id)

    db.commit()
    return True

def update_weight_entry(user_id, entry_id, weight, date_str, notes=None):
    """Atualiza um registro de peso existente do usuário."""
    db = get_db()
    cursor = db.cursor()

    weight = float(weight)
    notes = str(notes or '').strip()

    cursor.execute('''
        UPDATE weight_history
        SET weight = ?, recorded_date = ?, notes = ?
        WHERE id = ? AND user_id = ?
    ''', (weight, date_str, notes, entry_id, user_id))

    sync_latest_profile_weight(cursor, user_id)

    db.commit()
    return True

def delete_weight_entry(user_id, entry_id):
    """Exclui uma medição do histórico de peso do usuário."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        DELETE FROM weight_history
        WHERE id = ? AND user_id = ?
    ''', (entry_id, user_id))

    sync_latest_profile_weight(cursor, user_id)

    db.commit()
    return True

def sync_latest_profile_weight(cursor, user_id):
    """Sincroniza o peso atual do perfil com a medição mais recente do histórico."""
    cursor.execute('''
        SELECT weight FROM weight_history
        WHERE user_id = ?
        ORDER BY recorded_date DESC, id DESC
        LIMIT 1
    ''', (user_id,))
    latest = cursor.fetchone()
    if latest:
        cursor.execute('''
            UPDATE user_profiles
            SET current_weight = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (latest['weight'], user_id))

def get_weight_history(user_id, limit=30):
    """Retorna o histórico de peso registrado ordenado por data ascendente para gráficos."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, weight, recorded_date, notes, created_at
        FROM weight_history
        WHERE user_id = ?
        ORDER BY recorded_date ASC
        LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_dashboard_data(user_id, date_str=None):
    """Consolida todas as métricas para renderização da Dashboard."""
    if not date_str:
        date_str = get_today_date_str()

    profile = get_user_profile(user_id)
    diet_summary = get_daily_diet_summary(user_id, date_str)
    weight_history = get_weight_history(user_id, limit=30)
    caloric_history = get_caloric_history(user_id, days=7)
    streak_info = get_caloric_streak(user_id)

    # If no weight history exists yet, but profile exists, seed first weight history entry automatically
    if not weight_history and profile and profile.get('current_weight'):
        add_weight_entry(user_id, profile['current_weight'], date_str=date_str, notes='Peso inicial do perfil')
        weight_history = get_weight_history(user_id, limit=30)

    # Calculate weight progress statistics
    weight_stats = {
        'initial_weight': profile['current_weight'] if profile else 70.0,
        'current_weight': profile['current_weight'] if profile else 70.0,
        'target_weight': profile['current_weight'] if profile else 70.0,
        'weekly_rate_kg': profile['weekly_rate_kg'] if profile else 0.50,
        'weight_change_kg': 0.0,
        'progress_pct': 0,
        'remaining_kg': 0.0,
        'planned_weights': []
    }

    if profile:
        cur_w = profile['current_weight']
        change_meta = profile.get('target_weight_change_kg', 0.0)
        goal = profile.get('goal_type', 'maintenance')
        weekly_rate = profile.get('weekly_rate_kg', 0.50)

        if weight_history and len(weight_history) > 0:
            init_w = weight_history[0]['weight']
            try:
                first_date = datetime.datetime.strptime(weight_history[0]['recorded_date'], '%Y-%m-%d').date()
            except ValueError:
                first_date = datetime.date.today()
        else:
            init_w = cur_w
            first_date = datetime.date.today()

        if goal == 'weight_loss':
            target_w = profile.get('target_weight', init_w - change_meta)
            lost_so_far = max(0.0, init_w - cur_w)
            remaining = max(0.0, cur_w - target_w)
            progress = round((lost_so_far / change_meta * 100), 1) if change_meta > 0 else 100
        elif goal == 'weight_gain':
            target_w = profile.get('target_weight', init_w + change_meta)
            gained_so_far = max(0.0, cur_w - init_w)
            remaining = max(0.0, target_w - cur_w)
            progress = round((gained_so_far / change_meta * 100), 1) if change_meta > 0 else 100
        else: # maintenance
            target_w = init_w
            remaining = 0.0
            progress = 100

        # Calculate planned projection curve for history chart
        planned_weights = []
        for entry in weight_history:
            try:
                e_date = datetime.datetime.strptime(entry['recorded_date'], '%Y-%m-%d').date()
                days_diff = (e_date - first_date).days
            except ValueError:
                days_diff = 0
            
            weeks_diff = days_diff / 7.0

            if goal == 'weight_loss':
                planned_val = max(target_w, round(init_w - (weekly_rate * weeks_diff), 1))
            elif goal == 'weight_gain':
                planned_val = min(target_w, round(init_w + (weekly_rate * weeks_diff), 1))
            else:
                planned_val = init_w
                
            planned_weights.append(planned_val)

        weight_stats = {
            'initial_weight': round(init_w, 1),
            'current_weight': round(cur_w, 1),
            'target_weight': round(target_w, 1),
            'weekly_rate_kg': round(weekly_rate, 2),
            'change_meta': round(change_meta, 1),
            'progress_pct': min(100, max(0, int(progress))),
            'remaining_kg': round(remaining, 1),
            'planned_weights': planned_weights
        }

    return {
        'profile': profile,
        'diet': diet_summary,
        'weight_history': weight_history,
        'weight_stats': weight_stats,
        'caloric_history': caloric_history,
        'streak_info': streak_info,
        'current_date': date_str
    }
