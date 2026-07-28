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

    # Ensure source column exists if database was created previously
    cursor.execute("PRAGMA table_info(taco_foods)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'source' not in columns:
        cursor.execute("ALTER TABLE taco_foods ADD COLUMN source TEXT DEFAULT 'TACO'")

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

    # Seed TACO & TBCA Foods if empty or missing TBCA
    cursor.execute("SELECT COUNT(*) FROM taco_foods WHERE source = 'TACO'")
    if cursor.fetchone()[0] == 0:
        seed_taco_foods(cursor)

    cursor.execute("SELECT COUNT(*) FROM taco_foods WHERE source = 'TBCA'")
    if cursor.fetchone()[0] == 0:
        seed_tbca_foods(cursor)

    conn.commit()
    conn.close()

def seed_taco_foods(cursor):
    """Popular a tabela com alimentos de referência reais da TACO (UNICAMP). Values per 100g."""
    taco_data = [
        ("Arroz branco cozido", "Cereais e derivados", 128.0, 2.5, 28.1, 0.2, 1.6, "TACO"),
        ("Arroz integral cozido", "Cereais e derivados", 124.0, 2.6, 25.8, 1.0, 2.7, "TACO"),
        ("Feijão carioca cozido", "Leguminosas", 76.0, 4.8, 13.6, 0.5, 8.5, "TACO"),
        ("Feijão preto cozido", "Leguminosas", 77.0, 4.5, 14.0, 0.5, 8.4, "TACO"),
        ("Lentilha cozida", "Leguminosas", 93.0, 6.3, 16.3, 0.5, 7.9, "TACO"),
        ("Grão de bico cozido", "Leguminosas", 130.0, 7.0, 21.0, 2.6, 7.6, "TACO"),

        ("Peito de frango grelhado", "Carnes e ovos", 159.0, 32.0, 0.0, 2.5, 0.0, "TACO"),
        ("Peito de frango cozido", "Carnes e ovos", 150.0, 29.0, 0.0, 3.2, 0.0, "TACO"),
        ("Carne bovina patinho grelhado", "Carnes e ovos", 219.0, 35.9, 0.0, 7.3, 0.0, "TACO"),
        ("Carne bovina alcatra grelhada", "Carnes e ovos", 241.0, 31.9, 0.0, 11.6, 0.0, "TACO"),
        ("Carne moída bovina (acém) refogada", "Carnes e ovos", 212.0, 26.7, 0.0, 10.9, 0.0, "TACO"),
        ("Ovo de galinha cozido", "Carnes e ovos", 146.0, 13.3, 0.6, 9.5, 0.0, "TACO"),
        ("Ovo de galinha frito", "Carnes e ovos", 240.0, 15.6, 0.6, 18.6, 0.0, "TACO"),
        ("Omelete simples", "Carnes e ovos", 170.0, 11.0, 1.2, 13.0, 0.0, "TACO"),
        ("Clara de ovo cozida", "Carnes e ovos", 52.0, 11.0, 0.7, 0.2, 0.0, "TACO"),
        ("Filé de tilápia grelhado", "Carnes e ovos", 128.0, 26.0, 0.0, 2.7, 0.0, "TACO"),
        ("Filé de salmão grelhado", "Carnes e ovos", 229.0, 24.2, 0.0, 14.0, 0.0, "TACO"),
        ("Atum em conserva em óleo", "Carnes e ovos", 205.0, 26.5, 0.0, 11.0, 0.0, "TACO"),
        ("Atum em conserva em água", "Carnes e ovos", 116.0, 25.5, 0.0, 0.8, 0.0, "TACO"),
        ("Peito de peru defumado", "Carnes e ovos", 104.0, 21.0, 1.2, 1.6, 0.0, "TACO"),
        ("Presunto cozido", "Carnes e ovos", 128.0, 16.5, 2.1, 5.8, 0.0, "TACO"),

        ("Pão francês", "Cereais e derivados", 300.0, 8.0, 58.6, 3.1, 2.3, "TACO"),
        ("Pão de fôrma integral", "Cereais e derivados", 253.0, 9.4, 49.9, 3.7, 6.9, "TACO"),
        ("Pão de fôrma tradicional", "Cereais e derivados", 267.0, 8.2, 52.5, 2.8, 2.5, "TACO"),
        ("Batata doce cozida", "Tubérculos", 77.0, 0.6, 18.4, 0.1, 2.2, "TACO"),
        ("Batata inglesa cozida", "Tubérculos", 52.0, 1.2, 11.9, 0.1, 1.3, "TACO"),
        ("Mandioca cozida", "Tubérculos", 125.0, 0.6, 30.1, 0.3, 1.6, "TACO"),
        ("Macarrão cozido", "Cereais e derivados", 138.0, 4.5, 28.0, 0.7, 1.8, "TACO"),
        ("Tapioca pronta", "Cereais e derivados", 240.0, 0.0, 60.0, 0.2, 0.5, "TACO"),
        ("Aveia em flocos", "Cereais e derivados", 394.0, 13.9, 66.6, 8.5, 9.1, "TACO"),
        ("Cuscuz de milho cozido", "Cereais e derivados", 113.0, 2.2, 25.2, 0.7, 1.9, "TACO"),

        ("Leite de vaca integral", "Leite e derivados", 61.0, 3.2, 4.7, 3.4, 0.0, "TACO"),
        ("Leite desnatado", "Leite e derivados", 35.0, 3.4, 4.8, 0.1, 0.0, "TACO"),
        ("Leite semi-desnatado", "Leite e derivados", 45.0, 3.3, 4.8, 1.5, 0.0, "TACO"),
        ("Queijo muçarela", "Leite e derivados", 330.0, 22.6, 3.0, 25.2, 0.0, "TACO"),
        ("Queijo prato", "Leite e derivados", 360.0, 22.7, 1.9, 29.1, 0.0, "TACO"),
        ("Queijo minas frescal", "Leite e derivados", 264.0, 17.4, 3.2, 20.2, 0.0, "TACO"),
        ("Queijo cottage", "Leite e derivados", 98.0, 11.1, 3.4, 4.3, 0.0, "TACO"),
        ("Iogurte natural integral", "Leite e derivados", 51.0, 4.1, 3.8, 3.0, 0.0, "TACO"),
        ("Iogurte desnatado", "Leite e derivados", 41.0, 3.8, 5.8, 0.3, 0.0, "TACO"),
        ("Requeijão cremoso", "Leite e derivados", 257.0, 9.6, 2.4, 23.4, 0.0, "TACO"),

        ("Banana prata", "Frutas", 98.0, 1.3, 26.0, 0.3, 2.0, "TACO"),
        ("Banana caturra / nanica", "Frutas", 92.0, 1.4, 23.8, 0.1, 1.9, "TACO"),
        ("Maçã fuji", "Frutas", 56.0, 0.3, 15.2, 0.2, 1.3, "TACO"),
        ("Mamão papaia", "Frutas", 45.0, 0.5, 11.6, 0.1, 1.8, "TACO"),
        ("Laranja pera", "Frutas", 46.0, 1.0, 11.5, 0.1, 1.7, "TACO"),
        ("Morango", "Frutas", 30.0, 0.9, 6.8, 0.3, 1.7, "TACO"),
        ("Abacate", "Frutas", 96.0, 1.2, 6.0, 8.4, 6.3, "TACO"),
        ("Abacaxi", "Frutas", 48.0, 0.9, 12.3, 0.1, 1.0, "TACO"),
        ("Uva Itália", "Frutas", 53.0, 0.7, 13.6, 0.2, 0.9, "TACO"),
        ("Melancia", "Frutas", 33.0, 0.9, 8.1, 0.1, 0.1, "TACO"),

        ("Azeite de oliva extra virgem", "Óleos e gorduras", 884.0, 0.0, 0.0, 100.0, 0.0, "TACO"),
        ("Manteiga com sal", "Óleos e gorduras", 726.0, 0.4, 0.1, 82.0, 0.0, "TACO"),
        ("Óleo de soja", "Óleos e gorduras", 884.0, 0.0, 0.0, 100.0, 0.0, "TACO"),
        ("Castanha do Pará / do Brasil", "Nozes e sementes", 643.0, 14.5, 15.1, 63.5, 7.9, "TACO"),
        ("Amendoim torrado com sal", "Nozes e sementes", 606.0, 22.5, 18.7, 54.0, 8.0, "TACO"),
        ("Pasta de amendoim integral", "Nozes e sementes", 588.0, 25.0, 20.0, 50.0, 6.0, "TACO"),
        ("Whey Protein Concentrado 80%", "Suplementos", 390.0, 78.0, 8.0, 6.0, 0.0, "TACO"),
        ("Creatina em pó", "Suplementos", 0.0, 0.0, 0.0, 0.0, 0.0, "TACO"),

        ("Tomate cru", "Hortaliças", 15.0, 1.1, 3.1, 0.2, 1.2, "TACO"),
        ("Alface crespa crua", "Hortaliças", 11.0, 1.3, 1.7, 0.2, 1.4, "TACO"),
        ("Brócolis cozido", "Hortaliças", 25.0, 2.1, 4.4, 0.5, 3.4, "TACO"),
        ("Cenoura crua", "Hortaliças", 34.0, 1.3, 7.7, 0.2, 3.2, "TACO"),
        ("Chuchu cozido", "Hortaliças", 19.0, 0.4, 4.1, 0.2, 1.0, "TACO"),
        ("Couve manteiga refogada", "Hortaliças", 90.0, 2.7, 8.7, 5.7, 3.1, "TACO")
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO taco_foods (name, category, energy_kcal, protein_g, carbs_g, fat_g, fiber_g, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', taco_data)

def seed_tbca_foods(cursor):
    """Popular a tabela com alimentos preparados, pratos típicos e receitas comerciais da TBCA (USP). Values per 100g."""
    tbca_data = [
        ("Pizza de muçarela", "Pratos preparados", 270.0, 12.0, 28.5, 11.5, 1.5, "TBCA"),
        ("Pizza de calabresa", "Pratos preparados", 285.0, 13.0, 27.0, 13.5, 1.4, "TBCA"),
        ("Pizza de frango com requeijão", "Pratos preparados", 260.0, 14.5, 26.0, 11.0, 1.3, "TBCA"),
        ("Pizza de portuguesa", "Pratos preparados", 275.0, 13.5, 26.5, 12.0, 1.6, "TBCA"),
        ("Pão de queijo assado", "Salgados e lanches", 360.0, 6.5, 38.0, 20.0, 0.8, "TBCA"),
        ("Coxinha de frango frita", "Salgados e lanches", 250.0, 11.0, 24.0, 12.0, 1.1, "TBCA"),
        ("Pastel de carne frito", "Salgados e lanches", 310.0, 10.0, 31.0, 16.0, 1.2, "TBCA"),
        ("Pastel de queijo frito", "Salgados e lanches", 330.0, 11.0, 29.0, 19.0, 0.9, "TBCA"),
        ("Empada de frango", "Salgados e lanches", 320.0, 9.5, 32.0, 17.0, 1.0, "TBCA"),
        ("Kibe frito", "Salgados e lanches", 260.0, 14.0, 22.0, 13.0, 2.1, "TBCA"),

        ("Escondidinho de carne seca", "Pratos preparados", 180.0, 11.0, 16.0, 8.0, 1.5, "TBCA"),
        ("Strogonoff de frango", "Pratos preparados", 165.0, 15.5, 4.5, 9.5, 0.5, "TBCA"),
        ("Strogonoff de carne bovina", "Pratos preparados", 190.0, 17.0, 4.5, 11.5, 0.5, "TBCA"),
        ("Feijoada completa", "Pratos preparados", 145.0, 11.5, 9.0, 7.0, 3.2, "TBCA"),
        ("Lasanha à bolonhesa", "Pratos preparados", 185.0, 9.8, 17.5, 8.5, 1.2, "TBCA"),
        ("Panqueca de carne moída", "Pratos preparados", 175.0, 12.0, 15.0, 7.5, 0.9, "TBCA"),
        ("Moqueca de peixe", "Pratos preparados", 120.0, 13.0, 3.5, 6.0, 0.8, "TBCA"),
        ("Yakisoba de frango", "Pratos preparados", 140.0, 9.0, 18.0, 3.5, 1.5, "TBCA"),
        ("Risoto de camarão", "Pratos preparados", 160.0, 10.0, 20.0, 4.0, 0.7, "TBCA"),
        ("Salpicão de frango", "Pratos preparados", 155.0, 10.5, 6.5, 9.5, 1.2, "TBCA"),

        ("Açaí com xarope de guaraná", "Doces e sobremesas", 110.0, 1.2, 21.0, 2.5, 2.8, "TBCA"),
        ("Hambúrguer bovino grelhado", "Carnes e preparações", 240.0, 25.0, 0.0, 15.5, 0.0, "TBCA"),
        ("Batata frita", "Acompanhamentos", 312.0, 3.4, 41.0, 15.0, 3.8, "TBCA"),
        ("Omelete com queijo e presunto", "Ovos e preparações", 210.0, 15.0, 1.5, 16.0, 0.0, "TBCA"),
        ("Pão na chapa com manteiga", "Pães e torradas", 350.0, 7.0, 48.0, 14.0, 2.0, "TBCA"),
        ("Crepioca (ovo e tapioca)", "Ovos e preparações", 190.0, 10.0, 18.0, 8.0, 0.4, "TBCA"),
        ("Farofa de mandioca temperada", "Acompanhamentos", 410.0, 1.5, 75.0, 11.0, 3.5, "TBCA"),

        ("Bolo de cenoura com chocolate", "Doces e sobremesas", 360.0, 4.5, 54.0, 14.5, 1.4, "TBCA"),
        ("Biscoito recheado de chocolate", "Biscoitos e doces", 480.0, 6.0, 68.0, 20.0, 2.1, "TBCA"),
        ("Chocolate ao leite", "Doces e chocolates", 535.0, 7.5, 59.0, 30.0, 2.5, "TBCA"),
        ("Biscoito de polvilho assado", "Biscoitos e snacks", 430.0, 1.5, 74.0, 14.0, 1.0, "TBCA"),
        ("Brigadeiro de chocolate", "Doces e sobremesas", 380.0, 5.0, 56.0, 15.0, 1.1, "TBCA"),
        ("Pudim de leite condensado", "Doces e sobremesas", 240.0, 5.0, 38.0, 7.5, 0.0, "TBCA"),
        ("Mousse de maracujá", "Doces e sobremesas", 220.0, 3.5, 32.0, 9.0, 0.5, "TBCA"),
        ("Pipoca salgada com óleo", "Snacks e petiscos", 450.0, 8.0, 58.0, 22.0, 8.5, "TBCA"),

        ("Suco de laranja natural", "Bebidas", 45.0, 0.7, 10.4, 0.2, 0.4, "TBCA"),
        ("Suco de uva integral", "Bebidas", 60.0, 0.3, 14.5, 0.1, 0.2, "TBCA"),
        ("Refrigerante tipo cola", "Bebidas", 42.0, 0.0, 10.6, 0.0, 0.0, "TBCA"),
        ("Cerveja pilsen", "Bebidas", 43.0, 0.5, 3.5, 0.0, 0.0, "TBCA")
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO taco_foods (name, category, energy_kcal, protein_g, carbs_g, fat_g, fiber_g, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', tbca_data)
