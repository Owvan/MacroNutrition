import datetime
from app.database import get_db
from app.services.taco_services import get_taco_food_by_id
from app.services.macro_services import get_latest_user_macro

DEFAULT_MEAL_NAMES = ["Café da Manhã", "Almoço", "Lanche da Tarde", "Jantar"]

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
            SELECT id, meal_id, taco_food_id, food_name, amount_g, calories, protein_g, carbs_g, fat_g, created_at
            FROM user_meal_items
            WHERE meal_id = ?
            ORDER BY id ASC
        ''', (meal['id'],))
        items = [dict(row) for row in cursor.fetchall()]
        meal['food_items'] = items
        
        meal['total_calories'] = round(sum(i['calories'] for i in items), 1)
        meal['total_protein'] = round(sum(i['protein_g'] for i in items), 1)
        meal['total_carbs'] = round(sum(i['carbs_g'] for i in items), 1)
        meal['total_fat'] = round(sum(i['fat_g'] for i in items), 1)

    return meals

def add_user_meal(user_id, meal_name, meal_date=None):
    if not meal_date:
        meal_date = get_today_date_str()
    meal_name = meal_name.strip()
    if not meal_name:
        return False, "O nome da refeição é obrigatório."

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO user_meals (user_id, meal_date, meal_name)
        VALUES (?, ?, ?)
    ''', (user_id, meal_date, meal_name))
    db.commit()
    return True, cursor.lastrowid

def delete_user_meal(user_id, meal_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM user_meals WHERE id = ? AND user_id = ?', (meal_id, user_id))
    db.commit()
    return cursor.rowcount > 0

def add_food_to_meal(meal_id, taco_food_id, amount_g, custom_name=None, custom_kcal=0, custom_p=0, custom_c=0, custom_f=0):
    amount_g = float(amount_g)
    if amount_g <= 0:
        return False, "A quantidade em gramas deve ser maior que zero."

    db = get_db()
    cursor = db.cursor()

    if taco_food_id:
        food = get_taco_food_by_id(taco_food_id)
        if not food:
            return False, "Alimento não encontrado na tabela TACO."
        
        food_name = food['name']
        factor = amount_g / 100.0
        calories = round(food['energy_kcal'] * factor, 1)
        protein_g = round(food['protein_g'] * factor, 1)
        carbs_g = round(food['carbs_g'] * factor, 1)
        fat_g = round(food['fat_g'] * factor, 1)
    else:
        food_name = custom_name or "Alimento Personalizado"
        factor = amount_g / 100.0
        calories = round(float(custom_kcal) * factor, 1)
        protein_g = round(float(custom_p) * factor, 1)
        carbs_g = round(float(custom_c) * factor, 1)
        fat_g = round(float(custom_f) * factor, 1)

    cursor.execute('''
        INSERT INTO user_meal_items
        (meal_id, taco_food_id, food_name, amount_g, calories, protein_g, carbs_g, fat_g)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (meal_id, taco_food_id, food_name, amount_g, calories, protein_g, carbs_g, fat_g))
    db.commit()
    return True, cursor.lastrowid

def delete_meal_item(user_id, item_id):
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
