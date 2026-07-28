import uuid
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
from app.services.geo_services import processar_planilha_clientes, gerar_planilha_exportacao
from app.services.cep_services import get_cep_details, DB_PATH
from app.routes.auth_routes import login_required, admin_required

main = Blueprint("main", __name__)

# Cache em memória global para as análises dos usuários (evita estourar o limite de 4KB do cookie de sessão do Flask)
ANALYSES = {}

@main.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        try:
            # Capturar listas do formulário dinâmico
            nomes_unidades = request.form.getlist("nome_unidade[]")
            ceps_unidades = request.form.getlist("cep_unidade[]")
            raio_raw = request.form.get("raio", "300")
            
            # Validar e converter raio
            try:
                raio = float(raio_raw)
            except ValueError:
                raio = 300.0
                
            arquivo = request.files.get("planilha")
            
            if not ceps_unidades:
                flash("Por favor, informe pelo menos uma unidade da empresa.", "warning")
                return redirect(url_for("main.home"))
                
            if not arquivo or arquivo.filename == "":
                flash("Por favor, selecione uma planilha para análise.", "warning")
                return redirect(url_for("main.home"))
                
            # Agrupar pares de nome e cep
            matrizes_input = []
            for n, c in zip(nomes_unidades, ceps_unidades):
                c_clean = c.strip()
                if c_clean:
                    matrizes_input.append({
                        "nome": n.strip(),
                        "cep": c_clean
                    })
                    
            if not matrizes_input:
                flash("Por favor, insira pelo menos um CEP válido para as unidades da empresa.", "warning")
                return redirect(url_for("main.home"))
                
            # Processar planilha com múltiplas matrizes nomeadas
            result = processar_planilha_clientes(
                file_stream=arquivo.stream,
                filename=arquivo.filename,
                matrizes_input=matrizes_input,
                raio_limite=raio
            )
            
            # Gerar ID único para salvar na memória
            analysis_id = str(uuid.uuid4())
            ANALYSES[analysis_id] = {
                "matrizes": result["matrizes"],
                "clientes": result["clientes"],
                "resumo": result["resumo"],
                "df": result["df_resultado"]
            }
            
            # Guardar o ID de referência na sessão do usuário
            session["analysis_id"] = analysis_id
            
            # Feedback sobre unidades ignoradas, se houver
            if result["resumo"]["matrizes_descartadas"] > 0:
                flash(f"Aviso: {result['resumo']['matrizes_descartadas']} unidade(s) informada(s) tinha(m) CEPs inválidos/não localizados e foram ignoradas.", "warning")
                
            flash(f"Planilha processada com sucesso! {result['resumo']['total']} clientes analisados contra {result['resumo']['total_matrizes']} unidade(s) de atendimento.", "success")
            return redirect(url_for("main.resultados"))
            
        except Exception as e:
            flash(f"Erro no processamento: {str(e)}", "danger")
            return redirect(url_for("main.home"))
            
    return render_template("index.html")

@main.route("/resultados")
@login_required
def resultados():
    analysis_id = session.get("analysis_id")
    if not analysis_id or analysis_id not in ANALYSES:
        flash("Nenhuma análise ativa encontrada. Por favor, envie uma planilha primeiro.", "info")
        return redirect(url_for("main.home"))
        
    analysis = ANALYSES[analysis_id]
    return render_template(
        "resultados.html",
        matrizes=analysis["matrizes"],
        clientes=analysis["clientes"],
        resumo=analysis["resumo"]
    )

@main.route("/exportar")
@login_required
def exportar():
    analysis_id = session.get("analysis_id")
    if not analysis_id or analysis_id not in ANALYSES:
        flash("Nenhum resultado disponível para exportação.", "danger")
        return redirect(url_for("main.home"))
        
    analysis = ANALYSES[analysis_id]
    df = analysis["df"]
    
    excel_stream = gerar_planilha_exportacao(df)
    
    return send_file(
        excel_stream,
        as_attachment=True,
        download_name="resultado_distancias_cobertura.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@main.route("/cache", methods=["GET"])
@login_required
@admin_required
def cache_manager():
    # Conectar ao banco SQLite para listar os registros em cache
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Criar tabela se não existir
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
    
    # Obter contagem
    cursor.execute("SELECT COUNT(*) FROM cep_cache")
    total_cached = cursor.fetchone()[0]
    
    # Listar os últimos 100 CEPs resolvidos
    cursor.execute("""
        SELECT cep, municipio, uf, latitude, longitude, created_at 
        FROM cep_cache 
        ORDER BY created_at DESC 
        LIMIT 100
    """)
    rows = cursor.fetchall()
    conn.close()
    
    ceps_list = []
    for r in rows:
        ceps_list.append({
            "cep": r[0],
            "municipio": r[1],
            "uf": r[2],
            "latitude": r[3],
            "longitude": r[4],
            "created_at": r[5]
        })
        
    return render_template("cache.html", total=total_cached, ceps=ceps_list)

@main.route("/cache/adicionar", methods=["POST"])
@login_required
@admin_required
def cache_adicionar():
    cep = request.form.get("cep", "").strip()
    if not cep:
        flash("Digite um CEP válido para adicionar.", "warning")
        return redirect(url_for("main.cache_manager"))
        
    try:
        details = get_cep_details(cep)
        if details and details.get("latitude") is not None:
            flash(f"CEP {cep} adicionado/atualizado no cache local: {details.get('municipio')} - {details.get('uf')} ({details.get('latitude')}, {details.get('longitude')})", "success")
        elif details:
            flash(f"CEP {cep} resolvido, mas não foram encontradas coordenadas físicas: {details.get('municipio')} - {details.get('uf')}.", "warning")
        else:
            flash(f"Não foi possível encontrar ou resolver o CEP {cep}.", "danger")
    except Exception as e:
        flash(f"Erro ao pesquisar CEP: {str(e)}", "danger")
        
    return redirect(url_for("main.cache_manager"))

@main.route("/cache/limpar", methods=["POST"])
@login_required
@admin_required
def cache_limpar():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cep_cache")
        conn.commit()
        conn.close()
        flash("Todos os CEPs foram limpos do cache local com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao limpar cache: {str(e)}", "danger")
        
    return redirect(url_for("main.cache_manager"))

@main.route("/rotas", methods=["GET"])
@login_required
def rotas():
    # Carregar dados da análise ativa na sessão, se houver
    analysis_id = session.get("analysis_id")
    has_active_analysis = False
    matrizes = []
    clientes = []
    
    if analysis_id and analysis_id in ANALYSES:
        analysis = ANALYSES[analysis_id]
        matrizes = analysis["matrizes"]
        # Filtrar apenas clientes que possuem coordenadas geográficas válidas
        clientes = [c for c in analysis["clientes"] if c["latitude"] is not None and c["longitude"] is not None]
        has_active_analysis = True
        
    return render_template(
        "rotas.html",
        has_active_analysis=has_active_analysis,
        matrizes=matrizes,
        clientes=clientes
    )