import urllib.request
import urllib.parse
import json
import re
from app.database import get_db

HEADERS = {
    'User-Agent': 'MacroNutritionApp/1.0 (contact@macronutrition.app - Python/Flask)',
    'Accept': 'application/json'
}

DOMAINS = [
    'https://world.openfoodfacts.org',
    'https://us.openfoodfacts.org',
    'https://fr.openfoodfacts.org'
]

def save_off_product_to_db(name, category, energy_kcal, protein_g, carbs_g, fat_g, fiber_g=0):
    """Salva um produto do Open Food Facts no banco de dados SQLite local para buscas futuras sem API."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO taco_foods (name, category, energy_kcal, protein_g, carbs_g, fat_g, fiber_g, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'OFF')
        ''', (name, category, energy_kcal, protein_g, carbs_g, fat_g, fiber_g))
        db.commit()
    except Exception as e:
        print(f"Erro ao salvar produto no SQLite: {e}")

def fetch_product_by_barcode(barcode):
    """Consulta um produto no SQLite local primeiro ou na API Open Food Facts pelo Código de Barras (EAN)."""
    barcode_clean = re.sub(r'\D', '', str(barcode))
    if not barcode_clean:
        return {'found': False, 'error': 'Código de barras inválido.'}

    # 1. Check local SQLite first
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, name, category, energy_kcal, protein_g, carbs_g, fat_g, fiber_g, source
        FROM taco_foods
        WHERE name LIKE ?
        LIMIT 1
    ''', (f"%{barcode_clean}%",))
    row = cursor.fetchone()
    if row:
        r = dict(row)
        return {
            'found': True,
            'name': r['name'],
            'barcode': barcode_clean,
            'energy_kcal': r['energy_kcal'],
            'protein_g': r['protein_g'],
            'carbs_g': r['carbs_g'],
            'fat_g': r['fat_g'],
            'fiber_g': r['fiber_g'],
            'category': r['category']
        }

    # 2. Fetch from API with domain redundancy
    for domain in DOMAINS:
        url = f"{domain}/api/v0/product/{barcode_clean}.json"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    if data.get('status') == 1 and 'product' in data:
                        product = data['product']
                        name = product.get('product_name_pt') or product.get('product_name') or 'Produto sem nome'
                        brands = product.get('brands') or ''
                        
                        full_name = f"{name} ({brands})" if brands else name
                        nutriments = product.get('nutriments', {})

                        energy_kcal = nutriments.get('energy-kcal_100g')
                        if energy_kcal is None:
                            energy_kj = nutriments.get('energy_100g', 0)
                            energy_kcal = (float(energy_kj) / 4.184) if energy_kj else 0

                        protein_g = nutriments.get('proteins_100g', 0)
                        carbs_g = nutriments.get('carbohydrates_100g', 0)
                        fat_g = nutriments.get('fat_100g', 0)
                        fiber_g = nutriments.get('fiber_100g', 0)

                        result_item = {
                            'found': True,
                            'name': full_name.strip(),
                            'barcode': barcode_clean,
                            'energy_kcal': round(float(energy_kcal or 0), 1),
                            'protein_g': round(float(protein_g or 0), 1),
                            'carbs_g': round(float(carbs_g or 0), 1),
                            'fat_g': round(float(fat_g or 0), 1),
                            'fiber_g': round(float(fiber_g or 0), 1),
                            'category': 'Open Food Facts'
                        }

                        # Auto-persist into local SQLite database
                        save_off_product_to_db(
                            result_item['name'],
                            result_item['category'],
                            result_item['energy_kcal'],
                            result_item['protein_g'],
                            result_item['carbs_g'],
                            result_item['fat_g'],
                            result_item['fiber_g']
                        )

                        return result_item
        except Exception:
            continue

    return {'found': False, 'error': f'Nenhum produto localizado para o código EAN {barcode_clean}.'}

def search_openfoodfacts_by_name(query, limit=12):
    """Busca produtos por nome na API Open Food Facts e auto-salva no SQLite local."""
    if not query or len(query.strip()) < 2:
        return []

    safe_query = urllib.parse.quote(query.strip())

    for domain in DOMAINS:
        url = f"{domain}/cgi/search.pl?search_terms={safe_query}&search_simple=1&action=process&json=1&page_size={limit}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    products = data.get('products', [])
                    if products:
                        results = []
                        for p in products:
                            name = p.get('product_name_pt') or p.get('product_name')
                            if not name or len(name.strip()) == 0:
                                continue

                            brands = p.get('brands', '')
                            full_name = f"{name} ({brands})" if brands else name
                            nutriments = p.get('nutriments', {})

                            energy_kcal = nutriments.get('energy-kcal_100g')
                            if energy_kcal is None:
                                energy_kj = nutriments.get('energy_100g', 0)
                                energy_kcal = (float(energy_kj) / 4.184) if energy_kj else 0

                            item = {
                                'id': None,
                                'name': full_name.strip(),
                                'category': 'Open Food Facts',
                                'energy_kcal': round(float(energy_kcal or 0), 1),
                                'protein_g': round(float(nutriments.get('proteins_100g', 0) or 0), 1),
                                'carbs_g': round(float(nutriments.get('carbohydrates_100g', 0) or 0), 1),
                                'fat_g': round(float(nutriments.get('fat_100g', 0) or 0), 1),
                                'fiber_g': round(float(nutriments.get('fiber_100g', 0) or 0), 1),
                                'source': 'OFF'
                            }
                            results.append(item)

                            # Auto-persist into SQLite for instant future offline searches
                            save_off_product_to_db(
                                item['name'],
                                item['category'],
                                item['energy_kcal'],
                                item['protein_g'],
                                item['carbs_g'],
                                item['fat_g'],
                                item['fiber_g']
                            )

                        if results:
                            return results
        except Exception:
            continue

    return []
