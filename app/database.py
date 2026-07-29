import sqlite3
import os
import json
from flask import g

DB_NAME = "macronutrition.db"

def get_db_path():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, DB_NAME)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(get_db_path())
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # User table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # User Profiles & Goals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            full_name TEXT,
            gender TEXT DEFAULT 'male',
            age INTEGER DEFAULT 25,
            height REAL DEFAULT 170.0,
            current_weight REAL DEFAULT 70.0,
            goal_type TEXT DEFAULT 'weight_loss',
            target_weight_change_kg REAL DEFAULT 0.0,
            target_timeframe_weeks INTEGER DEFAULT 8,
            weekly_pace TEXT DEFAULT 'recommended',
            activity_level REAL DEFAULT 1.2,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    ''')

    cursor.execute("PRAGMA table_info(user_profiles)")
    prof_cols = [row[1] for row in cursor.fetchall()]
    if 'weekly_pace' not in prof_cols:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN weekly_pace TEXT DEFAULT 'recommended'")

    # BMR Records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bmr_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            gender TEXT NOT NULL,
            weight REAL NOT NULL,
            height REAL NOT NULL,
            age INTEGER NOT NULL,
            activity_level REAL NOT NULL,
            activity_label TEXT NOT NULL,
            bmr REAL NOT NULL,
            tdee REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    ''')

    # Macro Records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS macro_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            target_calories REAL NOT NULL,
            carb_pct REAL NOT NULL,
            protein_pct REAL NOT NULL,
            fat_pct REAL NOT NULL,
            carb_g REAL NOT NULL,
            protein_g REAL NOT NULL,
            fat_g REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    ''')

    # TACO & TBCA Foods table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS taco_foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            energy_kcal REAL NOT NULL,
            protein_g REAL NOT NULL,
            carbs_g REAL NOT NULL,
            fat_g REAL NOT NULL,
            fiber_g REAL DEFAULT 0,
            source TEXT DEFAULT 'TACO'
        );
    ''')

    cursor.execute("PRAGMA table_info(taco_foods)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'source' not in columns:
        cursor.execute("ALTER TABLE taco_foods ADD COLUMN source TEXT DEFAULT 'TACO'")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_taco_foods_name ON taco_foods(name);")

    # User Meals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            meal_date TEXT NOT NULL,
            meal_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
    ''')

    # User Meal Items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_meal_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meal_id INTEGER NOT NULL,
            taco_food_id INTEGER,
            food_name TEXT NOT NULL,
            amount_g REAL NOT NULL,
            unit_name TEXT DEFAULT 'g',
            unit_qty REAL DEFAULT 0,
            calories REAL NOT NULL,
            protein_g REAL NOT NULL,
            carbs_g REAL NOT NULL,
            fat_g REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meal_id) REFERENCES user_meals (id) ON DELETE CASCADE
        );
    ''')

    cursor.execute("PRAGMA table_info(user_meal_items)")
    meal_item_cols = [row[1] for row in cursor.fetchall()]
    if 'unit_name' not in meal_item_cols:
        cursor.execute("ALTER TABLE user_meal_items ADD COLUMN unit_name TEXT DEFAULT 'g'")
    if 'unit_qty' not in meal_item_cols:
        cursor.execute("ALTER TABLE user_meal_items ADD COLUMN unit_qty REAL DEFAULT 0")

    conn.commit()

    seed_foods_from_json(cursor)

    conn.commit()
    conn.close()

def seed_foods_from_json(cursor):
    """Carrega o acervo unificado da TACO (UNICAMP) e TBCA (USP) do arquivo foods_database.json para o SQLite."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'data', 'foods_database.json')

    if not os.path.exists(json_path):
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            foods_list = json.load(f)

        data_to_insert = [
            (
                item['name'],
                item['category'],
                float(item['energy_kcal']),
                float(item['protein_g']),
                float(item['carbs_g']),
                float(item['fat_g']),
                float(item.get('fiber_g', 0)),
                item.get('source', 'TACO')
            )
            for item in foods_list
        ]

        cursor.executemany('''
            INSERT OR IGNORE INTO taco_foods (name, category, energy_kcal, protein_g, carbs_g, fat_g, fiber_g, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', data_to_insert)
    except Exception as e:
        print(f"Erro ao popular banco a partir do arquivo JSON: {e}")
