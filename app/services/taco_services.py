import unicodedata
from app.database import get_db

_FOODS_CACHE = None

def strip_accents(text):
    if not text:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(text)) if unicodedata.category(c) != 'Mn').lower().strip()

def load_foods_cache():
    global _FOODS_CACHE
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, name, category, energy_kcal, protein_g, carbs_g, fat_g, fiber_g, source
        FROM taco_foods
    ''')
    rows = cursor.fetchall()
    
    cache = []
    for r in rows:
        item = dict(r)
        item['norm_name'] = strip_accents(item['name'])
        item['norm_category'] = strip_accents(item['category'])
        cache.append(item)
    
    _FOODS_CACHE = cache
    return _FOODS_CACHE

def search_taco_foods(query, limit=30):
    """
    Busca inteligente de alimentos com:
    1. Desacentuação automática (ex: pao -> pão, acai -> açaí)
    2. Multi-token (AND logic): 'frango grelhado' encontra 'Frango, peito, sem pele, grelhado'
    3. Algoritmo de relevância: prioriza itens diretos, TACO oficial e nomes concisos.
    """
    if not query or len(query.strip()) == 0:
        return []

    global _FOODS_CACHE
    if _FOODS_CACHE is None:
        load_foods_cache()

    norm_query = strip_accents(query)
    tokens = [t for t in norm_query.split() if len(t) > 0]
    if not tokens:
        return []

    scored_results = []

    for item in _FOODS_CACHE:
        norm_name = item['norm_name']
        norm_cat = item['norm_category']

        # Multi-token AND matching
        if not all(t in norm_name or t in norm_cat for t in tokens):
            continue

        # Relevance scoring algorithm
        score = 0.0

        # Exact match or starts with query
        if norm_name == norm_query:
            score += 1000.0
        elif norm_name.startswith(norm_query):
            score += 500.0
        elif norm_name.startswith(tokens[0]):
            score += 250.0

        # Word position bonus
        if tokens[0] in norm_name:
            pos = norm_name.find(tokens[0])
            if pos < 5:
                score += 100.0

        # TACO source bonus
        if item.get('source') == 'TACO':
            score += 120.0

        # Penalize super long recipe/botanical descriptions
        score -= len(item['name']) * 0.15

        scored_results.append((score, {
            'id': item['id'],
            'name': item['name'],
            'category': item['category'],
            'energy_kcal': item['energy_kcal'],
            'protein_g': item['protein_g'],
            'carbs_g': item['carbs_g'],
            'fat_g': item['fat_g'],
            'fiber_g': item['fiber_g'],
            'source': item.get('source', 'TACO')
        }))

    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored_results[:limit]]

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
