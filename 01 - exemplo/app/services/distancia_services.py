from geopy.distance import geodesic

def calcular_distancia(coord1, coord2):
    """
    Calcula a distância geodésica entre duas coordenadas (latitude, longitude).
    Retorna a distância em quilômetros (float) arredondada para duas casas decimais.
    Caso as coordenadas sejam inválidas ou nulas, retorna None.
    """
    try:
        if not coord1 or not coord2:
            return None
        
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return None
            
        dist = geodesic((lat1, lon1), (lat2, lon2)).kilometers
        return round(dist, 2)
    except Exception as e:
        print(f"Erro ao calcular distância entre {coord1} e {coord2}: {e}")
        return None
