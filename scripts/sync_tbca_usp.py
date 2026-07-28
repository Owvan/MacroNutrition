import urllib.request
import json
import os
import re

TBCA_RAW_URL = "https://raw.githubusercontent.com/raul-rznd/web-scraping-tbca/main/alimentos.txt"

def parse_float_val(val_str):
    if not val_str:
        return 0.0
    val_clean = str(val_str).replace(',', '.').strip()
    if val_clean in ['-', 'tr', 'NA', '']:
        return 0.0
    try:
        return float(val_clean)
    except ValueError:
        return 0.0

def clean_food_name(desc):
    if not desc:
        return ""
    # Clean redundant trailing commas and botanical terms in brackets if desired
    desc = re.sub(r',\s*$', '', desc.strip())
    return desc

def sync_tbca_usp_full():
    """Baixa e processa os 5.668 alimentos oficiais da TBCA (USP 5.0)."""
    print(f"Conectando ao repositório para baixar todos os 5.668 alimentos da TBCA (USP)...")
    headers = {'User-Agent': 'MacroNutrition/1.0'}
    
    try:
        req = urllib.request.Request(TBCA_RAW_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode('utf-8')
            lines = content.splitlines()
            print(f"Linhas recebidas: {len(lines)}")
            
            parsed_foods = []
            seen_names = set()

            for line in lines:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    raw_name = item.get('descricao', '')
                    name = clean_food_name(raw_name)
                    category = item.get('classe', 'Geral').strip()

                    if not name or name in seen_names:
                        continue

                    energy_kcal = 0.0
                    protein_g = 0.0
                    carbs_g = 0.0
                    fat_g = 0.0
                    fiber_g = 0.0

                    nutrientes = item.get('nutrientes', [])
                    for n in nutrientes:
                        comp = n.get('Componente', '').strip()
                        unit = n.get('Unidades', '').strip()
                        val = parse_float_val(n.get('Valor por 100g'))

                        if comp == 'Energia' and unit == 'kcal':
                            energy_kcal = val
                        elif 'Proteína' in comp:
                            protein_g = val
                        elif 'Carboidrato' in comp:
                            carbs_g = val
                        elif 'Lipídeo' in comp or 'Lipídios' in comp:
                            fat_g = val
                        elif 'Fibra' in comp:
                            fiber_g = val

                    parsed_foods.append({
                        'name': name,
                        'category': category,
                        'energy_kcal': round(energy_kcal, 1),
                        'protein_g': round(protein_g, 1),
                        'carbs_g': round(carbs_g, 1),
                        'fat_g': round(fat_g, 1),
                        'fiber_g': round(fiber_g, 1),
                        'source': 'TBCA'
                    })
                    seen_names.add(name)

                except Exception:
                    continue

            print(f"Alimentos únicos processados com sucesso: {len(parsed_foods)}")
            
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            target_json = os.path.join(base_dir, 'app', 'data', 'foods_database.json')

            with open(target_json, 'w', encoding='utf-8') as f:
                json.dump(parsed_foods, f, ensure_ascii=False, indent=2)

            print(f"Salvo em {target_json}!")
            return parsed_foods

    except Exception as e:
        print(f"Erro ao sincronizar TBCA USP: {e}")
        return []

if __name__ == '__main__':
    sync_tbca_usp_full()
