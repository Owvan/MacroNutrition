import datetime
from app.database import get_db, parse_float
from app.services.taco_services import get_taco_food_by_id
from app.services.macro_services import get_latest_user_macro

DEFAULT_MEAL_NAMES = ["Café da Manhã", "Almoço", "Lanche da Tarde", "Jantar"]

UNIT_LABELS = {
    'g': 'g',
    'unidade': 'unid.',
    'colher_sopa': 'colher(es) de sopa',
    'colher_cha': 'colher(es) de chá',
    'concha': 'concha(s)',
    'xicara': 'xícara(s)',
    'fatia': 'fatia(s)'
}

def get_today_date_str():
    return datetime.date.today().strftime("%Y-%m-%d")

def get_user_meals_with_items(user_id, meal_date=None):
    """Retorna as refeições do usuário para a data com todos os seus alimentos."""
    if not meal_date:
        meal_date = get_today_date_str()

    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        SELECT id, meal_name, created_at
        FROM user_meals
        WHERE user_id = ? AND meal_date = ?
        ORDER BY id ASC
    ''', (user_id, meal_date))
    meals = [dict(row) for row in cursor.fetchall()]

    if not meals:
        for name in DEFAULT_MEAL_NAMES:
            cursor.execute('''
                INSERT INTO user_meals (user_id, meal_date, meal_name)
                VALUES (?, ?, ?)
            ''', (user_id, meal_date, name))
        db.commit()

        cursor.execute('''
            SELECT id, meal_name, created_at
            FROM user_meals
            WHERE user_id = ? AND meal_date = ?
            ORDER BY id ASC
        ''', (user_id, meal_date))
        meals = [dict(row) for row in cursor.fetchall()]

    for meal in meals:
        cursor.execute('''
            SELECT id, meal_id, taco_food_id, food_name, amount_g, unit_name, unit_qty, calories, protein_g, carbs_g, fat_g, created_at
            FROM user_meal_items
            WHERE meal_id = ?
            ORDER BY id ASC
        ''', (meal['id'],))
        items = [dict(row) for row in cursor.fetchall()]

        for item in items:
            u_name = item.get('unit_name') or 'g'
            u_qty = item.get('unit_qty') or 0
            if u_name != 'g' and u_qty > 0:
                label = UNIT_LABELS.get(u_name, u_name)
                qty_str = int(u_qty) if u_qty == int(u_qty) else round(u_qty, 1)
                item['display_amount'] = f"{qty_str} {label} ({int(item['amount_g'])} g)"
            else:
                item['display_amount'] = f"{int(item['amount_g'])} g"

        meal['food_items'] = items
        
        meal['total_calories'] = round(sum(i['calories'] for i in items), 1)
        meal['total_protein'] = round(sum(i['protein_g'] for i in items), 1)
        meal['total_carbs'] = round(sum(i['carbs_g'] for i in items), 1)
        meal['total_fat'] = round(sum(i['fat_g'] for i in items), 1)

    return meals


def add_user_meal(user_id, meal_name, meal_date=None):
    """Cria uma nova refeição personalizada para a data informada."""
    if not meal_date:
        meal_date = get_today_date_str()

    meal_name = meal_name.strip()
    if not meal_name:
        return False, "O nome da refeição não pode ser vazio."

    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        INSERT INTO user_meals (user_id, meal_date, meal_name)
        VALUES (?, ?, ?)
    ''', (user_id, meal_date, meal_name))
    db.commit()

    return True, cursor.lastrowid


def delete_user_meal(user_id, meal_id):
    """Exclui uma refeição e todos os seus itens (via foreign key cascade)."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        DELETE FROM user_meals
        WHERE id = ? AND user_id = ?
    ''', (meal_id, user_id))
    db.commit()

    return cursor.rowcount > 0


def add_food_to_meal(user_id, meal_id, taco_food_id=None, amount_g=100, custom_name=None, custom_kcal=None, custom_p=None, custom_c=None, custom_f=None, unit_name='g', unit_qty=0):
    """
    Registra um alimento dentro de uma refeição específica do usuário logado (segurança IDOR).
    Pode ser da tabela TACO/TBCA ou alimento customizado/código de barras.
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        SELECT id FROM user_meals
        WHERE id = ? AND user_id = ?
    ''', (meal_id, user_id))
    meal_row = cursor.fetchone()

    if not meal_row:
        return False, "Refeição não encontrada ou permissão negada."

    amount_g = parse_float(amount_g, 100.0)
    unit_qty = parse_float(unit_qty, 0.0)
    if amount_g <= 0:
        return False, "Quantidade em gramas inválida."

    factor = amount_g / 100.0

    if taco_food_id:
        food = get_taco_food_by_id(taco_food_id)
        if not food:
            return False, "Alimento não encontrado na tabela nutricional."

        food_name = food['name']
        calories = round((food.get('energy_kcal') or food.get('energy_kcal', 0.0)) * factor, 1)
        protein_g = round((food.get('protein_g') if food.get('protein_g') is not None else food.get('protein_g', 0.0)) * factor, 1)
        carbs_g = round((food.get('carbs_g') if food.get('carbs_g') is not None else food.get('carbohydrate_g', 0.0)) * factor, 1)
        fat_g = round((food.get('fat_g') if food.get('fat_g') is not None else food.get('lipid_g', 0.0)) * factor, 1)
        t_id = taco_food_id

    else:
        if not custom_name:
            return False, "Informe o nome do alimento."

        food_name = custom_name.strip()
        base_kcal = parse_float(custom_kcal, 0.0)
        base_p = parse_float(custom_p, 0.0)
        base_c = parse_float(custom_c, 0.0)
        base_f = parse_float(custom_f, 0.0)

        calories = round(base_kcal * factor, 1)
        protein_g = round(base_p * factor, 1)
        carbs_g = round(base_c * factor, 1)
        fat_g = round(base_f * factor, 1)
        t_id = None

    cursor.execute('''
        INSERT INTO user_meal_items (meal_id, taco_food_id, food_name, amount_g, unit_name, unit_qty, calories, protein_g, carbs_g, fat_g)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (meal_id, t_id, food_name, amount_g, unit_name, unit_qty, calories, protein_g, carbs_g, fat_g))

    db.commit()
    return True, cursor.lastrowid


def delete_meal_item(user_id, item_id):
    """Exclui um item de alimento da refeição pertencente ao usuário logado."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        DELETE FROM user_meal_items
        WHERE id = ? AND meal_id IN (SELECT id FROM user_meals WHERE user_id = ?)
    ''', (item_id, user_id))
    db.commit()
    return cursor.rowcount > 0


def get_daily_diet_summary(user_id, meal_date=None):
    if not meal_date:
        meal_date = get_today_date_str()

    meals = get_user_meals_with_items(user_id, meal_date)
    latest_macro = get_latest_user_macro(user_id)

    target_cal = latest_macro['target_calories'] if latest_macro else 2000.0
    target_carb_g = latest_macro['carb_g'] if latest_macro else 250.0
    target_protein_g = latest_macro['protein_g'] if latest_macro else 100.0
    target_fat_g = latest_macro['fat_g'] if latest_macro else 66.0

    consumed_cal = round(sum(m['total_calories'] for m in meals), 1)
    consumed_protein_g = round(sum(m['total_protein'] for m in meals), 1)
    consumed_carbs_g = round(sum(m['total_carbs'] for m in meals), 1)
    consumed_fat_g = round(sum(m['total_fat'] for m in meals), 1)

    cal_pct = round((consumed_cal / target_cal) * 100, 1) if target_cal > 0 else 0
    protein_pct = round((consumed_protein_g / target_protein_g) * 100, 1) if target_protein_g > 0 else 0
    carb_pct = round((consumed_carbs_g / target_carb_g) * 100, 1) if target_carb_g > 0 else 0
    fat_pct = round((consumed_fat_g / target_fat_g) * 100, 1) if target_fat_g > 0 else 0

    return {
        'meal_date': meal_date,
        'meals': meals,
        'target_cal': target_cal,
        'target_carb_g': target_carb_g,
        'target_protein_g': target_protein_g,
        'target_fat_g': target_fat_g,
        'consumed_cal': consumed_cal,
        'consumed_protein_g': consumed_protein_g,
        'consumed_carbs_g': consumed_carbs_g,
        'consumed_fat_g': consumed_fat_g,
        'cal_pct': cal_pct,
        'protein_pct': protein_pct,
        'carb_pct': carb_pct,
        'fat_pct': fat_pct
    }


def get_caloric_history(user_id, days=7):
    """
    Retorna o histórico de consumo calórico diário dos últimos N dias retroativos.
    """
    db = get_db()
    cursor = db.cursor()

    latest_macro = get_latest_user_macro(user_id)
    target_cal = latest_macro['target_calories'] if latest_macro else 2000.0

    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=days - 1)

    cursor.execute('''
        SELECT m.meal_date, SUM(i.calories) as total_calories
        FROM user_meals m
        JOIN user_meal_items i ON m.id = i.meal_id
        WHERE m.user_id = ? AND m.meal_date >= ?
        GROUP BY m.meal_date
        ORDER BY m.meal_date ASC
    ''', (user_id, start_date.strftime("%Y-%m-%d")))

    rows = cursor.fetchall()
    consumed_by_date = {row['meal_date']: round(row['total_calories'] or 0.0, 1) for row in rows}

    history = []
    for i in range(days):
        day_date = start_date + datetime.timedelta(days=i)
        date_str = day_date.strftime("%Y-%m-%d")
        display_date = day_date.strftime("%d/%m")
        consumed = consumed_by_date.get(date_str, 0.0)
        within_target = (consumed > 0 and consumed <= target_cal * 1.05)
        exceeded = (consumed > target_cal * 1.05)

        history.append({
            'date': date_str,
            'display_date': display_date,
            'consumed_cal': consumed,
            'target_cal': target_cal,
            'within_target': within_target,
            'exceeded': exceeded
        })

    return history


def get_caloric_streak(user_id):
    """
    Calcula o sistema de Ofensiva (Streak) de dias consecutivos mantendo a meta de calorias.
    """
    db = get_db()
    cursor = db.cursor()

    latest_macro = get_latest_user_macro(user_id)
    target_cal = latest_macro['target_calories'] if latest_macro else 2000.0

    today = datetime.date.today()

    cursor.execute('''
        SELECT m.meal_date, SUM(i.calories) as total_calories
        FROM user_meals m
        JOIN user_meal_items i ON m.id = i.meal_id
        WHERE m.user_id = ?
        GROUP BY m.meal_date
        HAVING SUM(i.calories) > 0
        ORDER BY m.meal_date DESC
    ''', (user_id,))

    rows = cursor.fetchall()
    logged_days = {row['meal_date']: round(row['total_calories'] or 0.0, 1) for row in rows}

    streak_count = 0

    today_str = today.strftime("%Y-%m-%d")
    today_cal = logged_days.get(today_str, 0.0)

    if today_cal > 0 and today_cal <= target_cal * 1.05:
        streak_count += 1
        current = today - datetime.timedelta(days=1)
    else:
        current = today - datetime.timedelta(days=1)

    while True:
        c_str = current.strftime("%Y-%m-%d")
        c_cal = logged_days.get(c_str, 0.0)
        if c_cal > 0 and c_cal <= target_cal * 1.05:
            streak_count += 1
            current = current - datetime.timedelta(days=1)
        else:
            break

    if streak_count == 0:
        fire_icons = "❄️"
        level_title = "Sem Ofensiva Ativa"
        message = "Registre suas refeições hoje para acender o primeiro foguinho!"
        next_milestone = 3
        progress_pct = 0
    elif streak_count < 3:
        fire_icons = "🔥"
        level_title = "Foco Inicial"
        message = f"Excelente! {streak_count} dia(s) mantendo a meta. Continue assim!"
        next_milestone = 3
        progress_pct = int((streak_count / 3) * 100)
    elif streak_count < 7:
        fire_icons = "🔥🔥"
        level_title = "Ritmo Acelerado"
        message = f"Impressionante! {streak_count} dias em chamas. Faltam {7 - streak_count} dias para 1 semana!"
        next_milestone = 7
        progress_pct = int((streak_count / 7) * 100)
    elif streak_count < 14:
        fire_icons = "🔥🔥🔥"
        level_title = "Em Chamas (1+ Semana)"
        message = f"Sensacional! {streak_count} dias seguidos no foco nutricional!"
        next_milestone = 14
        progress_pct = int((streak_count / 14) * 100)
    elif streak_count < 30:
        fire_icons = "🔥🔥🔥🔥"
        level_title = "Consistência Imparável"
        message = f"Incrível! {streak_count} dias de disciplina pura. Rumo ao selo de Lenda!"
        next_milestone = 30
        progress_pct = int((streak_count / 30) * 100)
    else:
        fire_icons = "🏆 🔥🔥🔥🔥🔥"
        level_title = "Lenda da Nutrição"
        message = f"Imbatível! {streak_count} dias ininterruptos de ofensiva!"
        next_milestone = 30
        progress_pct = 100

    return {
        'streak_count': streak_count,
        'fire_icons': fire_icons,
        'level_title': level_title,
        'message': message,
        'next_milestone': next_milestone,
        'progress_pct': progress_pct
    }
