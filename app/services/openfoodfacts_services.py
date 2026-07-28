import urllib.request
import json
import re

HEADERS = {
    'User-Agent': 'MacroNutritionApp/1.0 (vinicius@macronutrition.app - Python/Flask)'
}

def fetch_product_by_barcode(barcode):
    """Consulta um produto na API Open Food Facts usando seu Código de Barras (EAN)."""
    barcode = re.sub(r'\D', '', str(barcode))
    if not barcode:
        return {'found': False, 'error': 'Código de barras inválido.'}

    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                return {'found': False, 'error': f'Erro de conexão com o servidor Open Food Facts (Status {response.status}).'}
            
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get('status') == 1 and 'product' in data:
                product = data['product']
                name = product.get('product_name_pt') or product.get('product_name') or 'Produto sem nome'
                brands = product.get('brands') or ''
                
                full_name = f"{name} ({brands})" if brands else name
                nutriments = product.get('nutriments', {})

                # Extract nutrients per 100g
                energy_kcal = nutriments.get('energy-kcal_100g')
                if energy_kcal is None:
                    energy_kj = nutriments.get('energy_100g', 0)
                    energy_kcal = energy_kj / 4.184 if energy_kj else 0

                protein_g = nutriments.get('proteins_100g', 0)
                carbs_g = nutriments.get('carbohydrates_100g', 0)
                fat_g = nutriments.get('fat_100g', 0)
                fiber_g = nutriments.get('fiber_100g', 0)

                return {
                    'found': True,
                    'name': full_name.strip(),
                    'barcode': barcode,
                    'energy_kcal': round(float(energy_kcal or 0), 1),
                    'protein_g': round(float(protein_g or 0), 1),
                    'carbs_g': round(float(carbs_g or 0), 1),
                    'fat_g': round(float(fat_g or 0), 1),
                    'fiber_g': round(float(fiber_g or 0), 1),
                    'category': 'Industrializado / Marcas'
                }
            else:
                return {'found': False, 'error': f'Nenhum produto encontrado para o código EAN {barcode}.'}
    except Exception as e:
        return {'found': False, 'error': f'Não foi possível consultar o código {barcode}: {str(e)}'}

def search_openfoodfacts_by_name(query, limit=10):
    """Busca produtos de supermercado por nome na API Open Food Facts Brasil."""
    if not query or len(query.strip()) < 2:
        return []

    safe_query = urllib.parse.quote(query.strip())
    url = f"https://br.openfoodfacts.org/cgi/search.pl?search_terms={safe_query}&search_simple=1&action=process&json=1&page_size={limit}"

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                return []
            
            data = json.loads(response.read().decode('utf-8'))
            products = data.get('products', [])
            results = []

            for p in products:
                name = p.get('product_name_pt') or p.get('product_name')
                if not name:
                    continue

                brands = p.get('brands', '')
                full_name = f"{name} ({brands})" if brands else name
                nutriments = p.get('nutriments', {})

                energy_kcal = nutriments.get('energy-kcal_100g')
                if energy_kcal is None:
                    energy_kj = nutriments.get('energy_100g', 0)
                    energy_kcal = energy_kj / 4.184 if energy_kj else 0

                results.append({
                    'id': None,
                    'name': full_name.strip(),
                    'category': 'Open Food Facts',
                    'energy_kcal': round(float(energy_kcal or 0), 1),
                    'protein_g': round(float(nutriments.get('proteins_100g', 0) or 0), 1),
                    'carbs_g': round(float(nutriments.get('carbohydrates_100g', 0) or 0), 1),
                    'fat_g': round(float(nutriments.get('fat_100g', 0) or 0), 1),
                    'fiber_g': round(float(nutriments.get('fiber_100g', 0) or 0), 1),
                    'source': 'OFF'
                })

            return results
    except Exception:
        return []
