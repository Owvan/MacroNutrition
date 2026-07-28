import sqlite3
import os
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

    # TACO Foods table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS taco_foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            energy_kcal REAL NOT NULL,
            protein_g REAL NOT NULL,
            carbs_g REAL NOT NULL,
            fat_g REAL NOT NULL,
            fiber_g REAL DEFAULT 0
        );
    ''')

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
            calories REAL NOT NULL,
            protein_g REAL NOT NULL,
            carbs_g REAL NOT NULL,
            fat_g REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (meal_id) REFERENCES user_meals (id) ON DELETE CASCADE
        );
    ''')

    conn.commit()

    # Seed TACO Foods if empty
    cursor.execute("SELECT COUNT(*) FROM taco_foods")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_taco_foods(cursor)
        conn.commit()

    conn.close()

def seed_taco_foods(cursor):
    """Popular a tabela TACO com alimentos de referência reais (UNICAMP). Values per 100g."""
    taco_data = [
        # (Nome, Categoria, kcal, proteina_g, carboidratos_g, gordura_g, fibra_g)
        ("Arroz branco cozido", "Cereais e derivados", 128.0, 2.5, 28.1, 0.2, 1.6),
        ("Arroz integral cozido", "Cereais e derivados", 124.0, 2.6, 25.8, 1.0, 2.7),
        ("Feijão carioca cozido", "Leguminosas", 76.0, 4.8, 13.6, 0.5, 8.5),
        ("Feijão preto cozido", "Leguminosas", 77.0, 4.5, 14.0, 0.5, 8.4),
        ("Lentilha cozida", "Leguminosas", 93.0, 6.3, 16.3, 0.5, 7.9),
        ("Grão de bico cozido", "Leguminosas", 130.0, 7.0, 21.0, 2.6, 7.6),

        ("Peito de frango grelhado", "Carnes e ovos", 159.0, 32.0, 0.0, 2.5, 0.0),
        ("Peito de frango cozido", "Carnes e ovos", 150.0, 29.0, 0.0, 3.2, 0.0),
        ("Carne bovina patinho grelhado", "Carnes e ovos", 219.0, 35.9, 0.0, 7.3, 0.0),
        ("Carne bovina alcatra grelhada", "Carnes e ovos", 241.0, 31.9, 0.0, 11.6, 0.0),
        ("Carne moída bovina (acém) refogada", "Carnes e ovos", 212.0, 26.7, 0.0, 10.9, 0.0),
        ("Ovo de galinha cozido", "Carnes e ovos", 146.0, 13.3, 0.6, 9.5, 0.0),
        ("Ovo de galinha frito", "Carnes e ovos", 240.0, 15.6, 0.6, 18.6, 0.0),
        ("Omelete simples", "Carnes e ovos", 170.0, 11.0, 1.2, 13.0, 0.0),
        ("Clara de ovo cozida", "Carnes e ovos", 52.0, 11.0, 0.7, 0.2, 0.0),
        ("Filé de tilápia grelhado", "Carnes e ovos", 128.0, 26.0, 0.0, 2.7, 0.0),
        ("Filé de salmão grelhado", "Carnes e ovos", 229.0, 24.2, 0.0, 14.0, 0.0),
        ("Atum em conserva em óleo", "Carnes e ovos", 205.0, 26.5, 0.0, 11.0, 0.0),
        ("Atum em conserva em água", "Carnes e ovos", 116.0, 25.5, 0.0, 0.8, 0.0),
        ("Peito de peru defumado", "Carnes e ovos", 104.0, 21.0, 1.2, 1.6, 0.0),
        ("Presunto cozido", "Carnes e ovos", 128.0, 16.5, 2.1, 5.8, 0.0),

        ("Pão francês", "Cereais e derivados", 300.0, 8.0, 58.6, 3.1, 2.3),
        ("Pão de fôrma integral", "Cereais e derivados", 253.0, 9.4, 49.9, 3.7, 6.9),
        ("Pão de fôrma tradicional", "Cereais e derivados", 267.0, 8.2, 52.5, 2.8, 2.5),
        ("Batata doce cozida", "Tubérculos", 77.0, 0.6, 18.4, 0.1, 2.2),
        ("Batata inglesa cozida", "Tubérculos", 52.0, 1.2, 11.9, 0.1, 1.3),
        ("Mandioca cozida", "Tubérculos", 125.0, 0.6, 30.1, 0.3, 1.6),
        ("Macarrão cozido", "Cereais e derivados", 138.0, 4.5, 28.0, 0.7, 1.8),
        ("Tapioca pronta", "Cereais e derivados", 240.0, 0.0, 60.0, 0.2, 0.5),
        ("Aveia em flocos", "Cereais e derivados", 394.0, 13.9, 66.6, 8.5, 9.1),
        ("Cuscuz de milho cozido", "Cereais e derivados", 113.0, 2.2, 25.2, 0.7, 1.9),

        ("Leite de vaca integral", "Leite e derivados", 61.0, 3.2, 4.7, 3.4, 0.0),
        ("Leite desnatado", "Leite e derivados", 35.0, 3.4, 4.8, 0.1, 0.0),
        ("Leite semi-desnatado", "Leite e derivados", 45.0, 3.3, 4.8, 1.5, 0.0),
        ("Queijo muçarela", "Leite e derivados", 330.0, 22.6, 3.0, 25.2, 0.0),
        ("Queijo prato", "Leite e derivados", 360.0, 22.7, 1.9, 29.1, 0.0),
        ("Queijo minas frescal", "Leite e derivados", 264.0, 17.4, 3.2, 20.2, 0.0),
        ("Queijo cottage", "Leite e derivados", 98.0, 11.1, 3.4, 4.3, 0.0),
        ("Iogurte natural integral", "Leite e derivados", 51.0, 4.1, 3.8, 3.0, 0.0),
        ("Iogurte desnatado", "Leite e derivados", 41.0, 3.8, 5.8, 0.3, 0.0),
        ("Requeijão cremoso", "Leite e derivados", 257.0, 9.6, 2.4, 23.4, 0.0),

        ("Banana prata", "Frutas", 98.0, 1.3, 26.0, 0.3, 2.0),
        ("Banana caturra / nanica", "Frutas", 92.0, 1.4, 23.8, 0.1, 1.9),
        ("Maçã fuji", "Frutas", 56.0, 0.3, 15.2, 0.2, 1.3),
        ("Mamão papaia", "Frutas", 45.0, 0.5, 11.6, 0.1, 1.8),
        ("Laranja pera", "Frutas", 46.0, 1.0, 11.5, 0.1, 1.7),
        ("Morango", "Frutas", 30.0, 0.9, 6.8, 0.3, 1.7),
        ("Abacate", "Frutas", 96.0, 1.2, 6.0, 8.4, 6.3),
        ("Abacaxi", "Frutas", 48.0, 0.9, 12.3, 0.1, 1.0),
        ("Uva Itália", "Frutas", 53.0, 0.7, 13.6, 0.2, 0.9),
        ("Melancia", "Frutas", 33.0, 0.9, 8.1, 0.1, 0.1),

        ("Azeite de oliva extra virgem", "Óleos e gorduras", 884.0, 0.0, 0.0, 100.0, 0.0),
        ("Manteiga com sal", "Óleos e gorduras", 726.0, 0.4, 0.1, 82.0, 0.0),
        ("Óleo de soja", "Óleos e gorduras", 884.0, 0.0, 0.0, 100.0, 0.0),
        ("Castanha do Pará / do Brasil", "Nozes e sementes", 643.0, 14.5, 15.1, 63.5, 7.9),
        ("Amendoim torrado com sal", "Nozes e sementes", 606.0, 22.5, 18.7, 54.0, 8.0),
        ("Pasta de amendoim integral", "Nozes e sementes", 588.0, 25.0, 20.0, 50.0, 6.0),
        ("Whey Protein Concentrado 80%", "Suplementos", 390.0, 78.0, 8.0, 6.0, 0.0),
        ("Creatina em pó", "Suplementos", 0.0, 0.0, 0.0, 0.0, 0.0),

        ("Tomate cru", "Hortaliças", 15.0, 1.1, 3.1, 0.2, 1.2),
        ("Alface crespa crua", "Hortaliças", 11.0, 1.3, 1.7, 0.2, 1.4),
        ("Brócolis cozido", "Hortaliças", 25.0, 2.1, 4.4, 0.5, 3.4),
        ("Cenoura crua", "Hortaliças", 34.0, 1.3, 7.7, 0.2, 3.2),
        ("Chuchu cozido", "Hortaliças", 19.0, 0.4, 4.1, 0.2, 1.0),
        ("Couve manteiga refogada", "Hortaliças", 90.0, 2.7, 8.7, 5.7, 3.1)
    ]

    cursor.executemany('''
        INSERT INTO taco_foods (name, category, energy_kcal, protein_g, carbs_g, fat_g, fiber_g)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', taco_data)
