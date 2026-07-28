import io
import pandas as pd
from app.services.cep_services import get_cep_details, clean_cep
from app.services.distancia_services import calcular_distancia

def find_column(columns, candidates):
    """
    Busca nas colunas do DataFrame aquela que mais se aproxima dos candidatos fornecidos.
    Retorna o nome exato da coluna ou None.
    """
    columns_lower = [str(c).lower().strip() for c in columns]
    for candidate in candidates:
        if candidate in columns_lower:
            idx = columns_lower.index(candidate)
            return columns[idx]
            
    # Busca por substring caso não encontre correspondência exata
    for candidate in candidates:
        for idx, col in enumerate(columns_lower):
            if candidate in col:
                return columns[idx]
                
    return None

def processar_planilha_clientes(file_stream, filename, matrizes_input, raio_limite=300.0):
    """
    Processa a planilha carregada (Excel ou CSV), resolve as localizações das unidades (matrizes/filiais)
    e dos clientes, e calcula a menor distância de cada cliente para a unidade mais próxima.
    
    matrizes_input: lista de dicionários contendo [{'nome': 'Unidade X', 'cep': '01310-100'}, ...]
    """
    # 1. Obter e geocodificar as localizações de todas as matrizes válidas
    valid_matrizes = []
    invalid_matrizes_count = 0
    
    for m in matrizes_input:
        nome_custom = m.get("nome", "").strip()
        cep_raw = m.get("cep", "").strip()
        cep_clean = clean_cep(cep_raw)
        
        if not cep_clean:
            invalid_matrizes_count += 1
            continue
            
        details = get_cep_details(cep_clean)
        if details and details.get("latitude") is not None:
            # Se o usuário não deu nome personalizado, gera um padrão baseado na cidade ou CEP
            nome_display = nome_custom if nome_custom else f"Unidade {details['municipio']}-{details['uf']}"
            
            valid_matrizes.append({
                "nome": nome_display,
                "cep": details["cep"],
                "municipio": details["municipio"],
                "uf": details["uf"],
                "latitude": details["latitude"],
                "longitude": details["longitude"]
            })
        else:
            invalid_matrizes_count += 1
            
    if not valid_matrizes:
        raise ValueError("Não foi possível geolocalizar nenhuma das unidades/matrizes da empresa informadas. Verifique se os CEPs de origem estão digitados corretamente.")
        
    # 2. Ler planilha com Pandas
    if filename.endswith('.csv'):
        try:
            df = pd.read_csv(file_stream, sep=';', encoding='utf-8')
        except Exception:
            try:
                file_stream.seek(0)
                df = pd.read_csv(file_stream, sep=',', encoding='utf-8')
            except Exception:
                file_stream.seek(0)
                df = pd.read_csv(file_stream, sep=';', encoding='latin1')
    else:
        df = pd.read_excel(file_stream)
        
    if df.empty:
        raise ValueError("A planilha enviada está vazia.")
        
    # 3. Detectar colunas de interesse na planilha
    col_nome_candidates = ['nome', 'cliente', 'nome cliente', 'name', 'client', 'razão social', 'razao social', 'empresa', 'destinatário', 'destinatario']
    col_cep_candidates = ['cep', 'c.e.p.', 'ceps', 'codigo postal', 'cod_postal', 'zip', 'zipcode']
    
    col_nome = find_column(df.columns, col_nome_candidates)
    col_cep = find_column(df.columns, col_cep_candidates)
    
    if not col_cep:
        raise ValueError("Não foi possível identificar a coluna de CEP na planilha. Certifique-se de ter uma coluna contendo o CEP de destino dos clientes (ex: 'CEP').")
        
    if not col_nome:
        df['Cliente_Detetado'] = [f"Cliente {i+1}" for i in range(len(df))]
        col_nome = 'Cliente_Detetado'
        
    # 4. Processar linhas
    clientes_resultado = []
    
    # Listas auxiliares para preencher novas colunas do DataFrame final
    cliente_municipios_list = []
    cliente_ufs_list = []
    cliente_lat_list = []
    cliente_lon_list = []
    
    matriz_proxima_nome_list = []
    matriz_proxima_cep_list = []
    matriz_proxima_cidade_list = []
    distancias_list = []
    status_list = []
    
    total_clientes = 0
    dentro_cobertura = 0
    fora_cobertura = 0
    invalidos = 0
    
    for idx, row in df.iterrows():
        nome_cli = str(row[col_nome]).strip()
        cep_raw = str(row[col_cep]).strip()
        cep_cli = clean_cep(cep_raw)
        
        municipio = "-"
        uf = "-"
        latitude = None
        longitude = None
        
        menor_distancia = None
        matriz_proxima = None
        status = "CEP Inválido"
        
        if cep_cli:
            details = get_cep_details(cep_cli)
            if details:
                municipio = details.get("municipio", "-")
                uf = details.get("uf", "-")
                latitude = details.get("latitude")
                longitude = details.get("longitude")
                
                if latitude is not None and longitude is not None:
                    # Calcular distâncias para TODAS as matrizes válidas e encontrar a menor
                    for mat in valid_matrizes:
                        dist = calcular_distancia((mat["latitude"], mat["longitude"]), (latitude, longitude))
                        if dist is not None:
                            if menor_distancia is None or dist < menor_distancia:
                                menor_distancia = dist
                                matriz_proxima = mat
                                
                    if menor_distancia is not None:
                        if menor_distancia <= raio_limite:
                            status = "Dentro da Cobertura"
                            dentro_cobertura += 1
                        else:
                            status = "Fora de Cobertura"
                            fora_cobertura += 1
                    else:
                        status = "Erro no Cálculo"
                        invalidos += 1
                else:
                    status = "Coordenadas Não Encontradas"
                    invalidos += 1
            else:
                status = "CEP Não Localizado"
                invalidos += 1
        else:
            status = "CEP Inválido"
            invalidos += 1
            
        total_clientes += 1
        
        # Obter dados da matriz mais próxima
        m_nome = matriz_proxima["nome"] if matriz_proxima else "-"
        m_cep = matriz_proxima["cep"] if matriz_proxima else "-"
        m_cidade = f"{matriz_proxima['municipio']}-{matriz_proxima['uf']}" if matriz_proxima else "-"
        m_lat = matriz_proxima["latitude"] if matriz_proxima else None
        m_lon = matriz_proxima["longitude"] if matriz_proxima else None
        
        # Guarda dados para renderização no front-end
        clientes_resultado.append({
            "id": idx + 1,
            "nome": nome_cli,
            "cep": cep_raw,
            "cep_limpo": cep_cli,
            "municipio": municipio,
            "uf": uf,
            "latitude": latitude,
            "longitude": longitude,
            "distancia": menor_distancia,
            "status": status,
            "matriz_proxima": {
                "nome": m_nome,
                "cep": m_cep,
                "cidade": m_cidade,
                "latitude": m_lat,
                "longitude": m_lon
            }
        })
        
        # Guarda informações para adicionar no DataFrame final
        cliente_municipios_list.append(municipio)
        cliente_ufs_list.append(uf)
        cliente_lat_list.append(latitude)
        cliente_lon_list.append(longitude)
        
        matriz_proxima_nome_list.append(m_nome)
        matriz_proxima_cep_list.append(m_cep)
        matriz_proxima_cidade_list.append(m_cidade)
        distancias_list.append(menor_distancia if menor_distancia is not None else "")
        status_list.append(status)
        
    # Adicionar as colunas calculadas ao DataFrame
    df['Cliente_Município'] = cliente_municipios_list
    df['Cliente_UF'] = cliente_ufs_list
    df['Cliente_Latitude'] = cliente_lat_list
    df['Cliente_Longitude'] = cliente_lon_list
    df['Matriz_Mais_Proxima_Nome'] = matriz_proxima_nome_list
    df['Matriz_Mais_Proxima_CEP'] = matriz_proxima_cep_list
    df['Matriz_Mais_Proxima_Cidade'] = matriz_proxima_cidade_list
    df['Distância_KM'] = distancias_list
    df['Status_Cobertura'] = status_list
    
    resumo = {
        "total": total_clientes,
        "dentro": dentro_cobertura,
        "fora": fora_cobertura,
        "invalidos": invalidos,
        "porcentagem_dentro": round((dentro_cobertura / total_clientes) * 100, 1) if total_clientes > 0 else 0,
        "raio": raio_limite,
        "total_matrizes": len(valid_matrizes),
        "matrizes_descartadas": invalid_matrizes_count
    }
    
    return {
        "matrizes": valid_matrizes,
        "clientes": clientes_resultado,
        "resumo": resumo,
        "df_resultado": df
    }

def gerar_planilha_exportacao(df):
    """
    Gera um arquivo Excel em memória contendo o DataFrame processado e retorna o stream.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultado Cobertura')
    output.seek(0)
    return output
