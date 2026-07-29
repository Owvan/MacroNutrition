from app.database import get_db

def search_taco_foods(query, limit=30):
    """Busca alimentos nas tabelas TACO e TBCA (USP) por termo de busca, priorizando TACO."""
    if not query or len(query.strip()) == 0:
        return []
    
    query = f"%{query.strip()}%"
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, name, category, energy_kcal, protein_g, carbs_g, fat_g, fiber_g, source
        FROM taco_foods
        WHERE name LIKE ? OR category LIKE ?
        ORDER BY 
            CASE WHEN source = 'TACO' THEN 0 ELSE 1 END,
            CASE WHEN name LIKE ? THEN 0 ELSE 1 END,
            name ASC
        LIMIT ?
    ''', (query, query, query, limit))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_taco_food_by_id(food_id):
    """Retorna os dados nutricionais por 100g de um alimento específico."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, name, category, energy_kcal, protein_g, carbs_g, fat_g, fiber_g, source
        FROM taco_foods
        WHERE id = ?
    ''', (food_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_all_taco_categories():
    """Retorna todas as categorias disponíveis nas tabelas TACO e TBCA."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT DISTINCT category FROM taco_foods ORDER BY category ASC')
    rows = cursor.fetchall()
    return [row['category'] for row in rows]
