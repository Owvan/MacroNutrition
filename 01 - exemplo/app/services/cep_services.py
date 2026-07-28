import sqlite3
import re
import requests
import os
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# O banco de dados ceps_cache.db ficará no diretório raiz do projeto
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ceps_cache.db")

def init_db():
    """Inicializa a tabela de cache de CEPs no banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cep_cache (
            cep TEXT PRIMARY KEY,
            municipio TEXT NOT NULL,
            uf TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def clean_cep(cep):
    """
    Remove qualquer caractere não numérico, trata floats do excel (ex: '8673000.0'),
    adiciona zeros à esquerda se faltarem e valida se o CEP possui 8 dígitos.
    """
    if cep is None:
        return ""
        
    cep_str = str(cep).strip()
    
    # Se o Pandas leu como float do Excel (ex: '8673000.0'), remover a parte decimal '.0'
    if "." in cep_str:
        parts = cep_str.split(".")
        if parts[1] == "0" or parts[1] == "":
            cep_str = parts[0]
            
    # Remover caracteres não numéricos
    cep_cleaned = re.sub(r"\D", "", cep_str)
    
    if not cep_cleaned:
        return ""
        
    # Preencher com zeros à esquerda se tiver menos de 8 dígitos (ex: '8673000' -> '08673000')
    if len(cep_cleaned) < 8:
        cep_cleaned = cep_cleaned.zfill(8)
        
    if len(cep_cleaned) == 8:
        return cep_cleaned
        
    return ""

def get_cep_from_cache(cep):
    """Busca o CEP no banco de dados SQLite local."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT municipio, uf, latitude, longitude FROM cep_cache WHERE cep = ?", (cep,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "cep": cep,
            "municipio": row[0],
            "uf": row[1],
            "latitude": row[2],
            "longitude": row[3],
            "cached": True
        }
    return None

def save_cep_to_cache(cep, municipio, uf, latitude, longitude):
    """Salva as informações do CEP no cache local."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO cep_cache (cep, municipio, uf, latitude, longitude)
            VALUES (?, ?, ?, ?, ?)
        """, (cep, municipio, uf, latitude, longitude))
        conn.commit()
    except Exception as e:
        print(f"Erro ao salvar CEP {cep} no cache: {e}")
    finally:
        conn.close()

def fetch_cep_from_api(cep):
    """Consulta as APIs públicas (BrasilAPI / ViaCEP) e tenta obter coordenadas."""
    cep_cleaned = clean_cep(cep)
    if not cep_cleaned:
        return None
    
    # 1. Tenta usar BrasilAPI v2 (que inclui latitude/longitude)
    try:
        url = f"https://brasilapi.com.br/api/cep/v2/{cep_cleaned}"
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            city = data.get("city", "")
            state = data.get("state", "")
            location = data.get("location", {})
            coords = location.get("coordinates", {})
            lat = coords.get("latitude")
            lon = coords.get("longitude")
            
            if lat is not None and lon is not None:
                return {
                    "cep": cep_cleaned,
                    "municipio": city,
                    "uf": state,
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "cached": False
                }
            else:
                return {
                    "cep": cep_cleaned,
                    "municipio": city,
                    "uf": state,
                    "latitude": None,
                    "longitude": None,
                    "cached": False
                }
    except Exception as e:
        print(f"Erro ao consultar BrasilAPI v2 para CEP {cep_cleaned}: {e}")

    # 2. Tenta usar ViaCEP (se o BrasilAPI falhar ou não retornar dados geográficos)
    try:
        url = f"https://viacep.com.br/ws/{cep_cleaned}/json/"
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            if "erro" not in data:
                return {
                    "cep": cep_cleaned,
                    "municipio": data.get("localidade", ""),
                    "uf": data.get("uf", ""),
                    "latitude": None,
                    "longitude": None,
                    "cached": False
                }
    except Exception as e:
        print(f"Erro ao consultar ViaCEP para CEP {cep_cleaned}: {e}")
        
    return None

def geocode_city(municipio, uf):
    """Usa Nominatim (geopy) para obter coordenadas do município/UF."""
    if not municipio or not uf:
        return None, None
    try:
        geolocator = Nominatim(user_agent="cep_distance_app_vinicius_v1")
        query = f"{municipio}, {uf}, Brazil"
        location = geolocator.geocode(query, timeout=8)
        if location:
            return location.latitude, location.longitude
    except (GeocoderTimedOut, Exception) as e:
        print(f"Erro ao geocodificar cidade {municipio}-{uf}: {e}")
    return None, None

def get_cep_details(cep):
    """
    Busca detalhes de um CEP.
    Checa o banco local; caso não exista, busca na API externa e geocodifica
    a cidade se necessário. Por fim, salva no SQLite local e retorna o resultado.
    """
    cep_cleaned = clean_cep(cep)
    if not cep_cleaned:
        return None
        
    # 1. Tentar obter do cache local
    cached_data = get_cep_from_cache(cep_cleaned)
    if cached_data:
        return cached_data
        
    # 2. Se não estiver no cache, consultar APIs de CEP
    api_data = fetch_cep_from_api(cep_cleaned)
    if not api_data:
        return None
        
    # 3. Se as coordenadas forem nulas, buscar geocodificação da cidade
    lat = api_data.get("latitude")
    lon = api_data.get("longitude")
    
    if lat is None or lon is None:
        lat, lon = geocode_city(api_data["municipio"], api_data["uf"])
        api_data["latitude"] = lat
        api_data["longitude"] = lon
        
    # 4. Salvar no cache local para pesquisas futuras (mesmo se coordenadas forem nulas,
    # para evitar re-consultar CEPs inválidos várias vezes)
    save_cep_to_cache(
        cep_cleaned, 
        api_data["municipio"], 
        api_data["uf"], 
        api_data["latitude"], 
        api_data["longitude"]
    )
    
    return api_data
