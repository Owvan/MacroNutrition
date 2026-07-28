import unittest
import os
import sqlite3
from flask import session
from app import create_app
from app.services.cep_services import DB_PATH
from app.services.auth_services import criar_usuario, verificar_usuario, seed_admin
from app.routes.main_routes import ANALYSES

class TestRoutingAccessControl(unittest.TestCase):
    
    def setUp(self):
        # Utilizar base de testes temporária
        self.test_db_path = "ceps_cache_test.db"
        
        # Monkey-patch para isolar o banco de dados principal
        import app.services.cep_services as cs
        import app.services.auth_services as as_serv
        import app.routes.main_routes as mr
        import app.routes.auth_routes as ar
        
        self.original_db_path = cs.DB_PATH
        cs.DB_PATH = self.test_db_path
        as_serv.DB_PATH = self.test_db_path
        mr.DB_PATH = self.test_db_path
        ar.DB_PATH = self.test_db_path
        
        # Instanciar Flask client
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.app.secret_key = "segredo-testes-rotas"
        self.client = self.app.test_client()
        
    def tearDown(self):
        # Restaurar caminhos originais
        import app.services.cep_services as cs
        import app.services.auth_services as as_serv
        import app.routes.main_routes as mr
        import app.routes.auth_routes as ar
        
        cs.DB_PATH = self.original_db_path
        as_serv.DB_PATH = self.original_db_path
        mr.DB_PATH = self.original_db_path
        ar.DB_PATH = self.original_db_path
        
        # Remover base temporária
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_rotas_route_blocks_unauthorized(self):
        # Tentar acessar sem estar logado -> Deve redirecionar para a página de login
        response = self.client.get("/rotas")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers.get("Location", ""))

    def test_rotas_route_loads_for_logged_in_user_without_analysis(self):
        # 1. Registrar e aprovar um usuário comum para testes
        criar_usuario("comum_rotas", "senha123")
        
        # Aprovar diretamente no banco para permitir o login
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET approved = 1 WHERE username = 'comum_rotas'")
        conn.commit()
        conn.close()
        
        # 2. Logar como o usuário comum
        self.client.post("/login", data={
            "username": "comum_rotas",
            "password": "senha123"
        }, follow_redirects=True)
        
        # 3. Acessar a página de planejamento (deve retornar 200 e carregar o painel manual por padrão)
        response = self.client.get("/rotas")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Montagem Manual", response.data.decode("utf-8"))
        self.assertIn("Ponto de Partida", response.data.decode("utf-8"))

    def test_rotas_route_loads_with_active_analysis_data(self):
        # 1. Logar como o administrador padrão
        self.client.post("/login", data={
            "username": "vinicius",
            "password": "Vi@250793l"
        }, follow_redirects=True)
        
        # 2. Injetar dados simulados de análise no cache em memória global e no cookie de sessão
        analysis_id = "test-analysis-routing-id"
        ANALYSES[analysis_id] = {
            "matrizes": [
                {"nome": "Matriz Principal", "cep": "01310-100", "municipio": "São Paulo", "uf": "SP", "latitude": -23.5615, "longitude": -46.6562}
            ],
            "clientes": [
                {"id": 1, "nome": "Cliente A", "cep": "08673-000", "municipio": "Suzano", "uf": "SP", "latitude": -23.5375, "longitude": -46.3088, "status": "Dentro da Cobertura", "matriz_proxima": {}}
            ],
            "resumo": {"total_matrizes": 1, "raio": 300},
            "df": None
        }
        
        # Configurar cookie de sessão do flask client
        with self.client.session_transaction() as sess:
            sess["analysis_id"] = analysis_id
            
        # 3. Acessar a página de rotas (deve carregar com a aba de análise ativa disponível)
        response = self.client.get("/rotas")
        self.assertEqual(response.status_code, 200)
        html_content = response.data.decode("utf-8")
        
        self.assertIn("Usar Análise Ativa", html_content)
        self.assertIn("Matriz Principal", html_content)
        self.assertIn("Cliente A", html_content)

if __name__ == "__main__":
    unittest.main()
