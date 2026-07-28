import unittest
import os
import sqlite3
from flask import session
from app import create_app
from app.services.cep_services import DB_PATH
from app.services.auth_services import criar_usuario, verificar_usuario, seed_admin

class TestAuthenticationApproval(unittest.TestCase):
    
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
        self.app.secret_key = "segredo-testes-aprova"
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

    def test_seeding_admin(self):
        # O admin deve ser criado pelo startup (que roda na setUp chamando create_app)
        # Vamos verificar se as credenciais do admin 'vinicius' foram criadas corretas e aprovadas
        admin = verificar_usuario("vinicius", "Vi@250793l")
        self.assertIsNotNone(admin)
        self.assertEqual(admin["username"], "vinicius")
        self.assertTrue(admin["approved"])
        self.assertTrue(admin["is_admin"])

    def test_usuario_comum_pendente_bloqueado(self):
        # 1. Registrar usuário comum
        criar_usuario("comum", "senha123")
        
        # 2. Verificar se ele foi criado como NÃO aprovado
        user_info = verificar_usuario("comum", "senha123")
        self.assertIsNotNone(user_info)
        self.assertFalse(user_info["approved"])
        self.assertFalse(user_info["is_admin"])
        
        # 3. Tentar fazer login (POST /login) -> Deve barrar por não estar aprovado
        response = self.client.post("/login", data={
            "username": "comum",
            "password": "senha123"
        }, follow_redirects=True)
        
        # Deve exibir a mensagem de aviso na página de login e não efetuar o login
        self.assertIn("Sua conta ainda não foi aprovada", response.data.decode("utf-8"))
        
        # Verificar que a sessão NÃO possui o id do usuário comum
        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)

    def test_admin_required_decorator_protection(self):
        # 1. Registrar e aprovar um usuário comum para testes
        criar_usuario("comum", "senha123")
        
        # Aprovar diretamente no banco para permitir o login
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET approved = 1 WHERE username = 'comum'")
        conn.commit()
        conn.close()
        
        # 2. Logar como o usuário comum
        self.client.post("/login", data={
            "username": "comum",
            "password": "senha123"
        }, follow_redirects=True)
        
        # 3. Tentar acessar rotas de administrador com a conta comum logada (Deve barrar e redirecionar para a Home)
        # Rota de visualização (/admin)
        response_get = self.client.get("/admin", follow_redirects=True)
        self.assertIn("Acesso negado: Esta operação requer privilégios de administrador.", response_get.data.decode("utf-8"))
        
        # Rota de ação (/admin/aprovar/1)
        response_post = self.client.post("/admin/aprovar/1", follow_redirects=True)
        self.assertIn("Acesso negado: Esta operação requer privilégios de administrador.", response_post.data.decode("utf-8"))
        
        # Nova Rota restrita: Banco de CEPs (/cache)
        response_cache = self.client.get("/cache", follow_redirects=True)
        self.assertIn("Acesso negado: Esta operação requer privilégios de administrador.", response_cache.data.decode("utf-8"))
        
        # Nova Rota restrita: Limpar cache (/cache/limpar)
        response_clear = self.client.post("/cache/limpar", follow_redirects=True)
        self.assertIn("Acesso negado: Esta operação requer privilégios de administrador.", response_clear.data.decode("utf-8"))

    def test_admin_flow_aprovacao_e_exclusao(self):
        # 1. Registrar usuário comum (inicia pendente)
        criar_usuario("gaby", "senha321")
        
        # 2. Logar como administrador
        self.client.post("/login", data={
            "username": "vinicius",
            "password": "Vi@250793l"
        }, follow_redirects=True)
        
        # Verificar que o admin está na sessão
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("username"), "vinicius")
            self.assertTrue(sess.get("is_admin"))
            
        # 3. Acessar o Painel Admin e verificar se o usuário 'gaby' está listado
        response_admin = self.client.get("/admin")
        self.assertEqual(response_admin.status_code, 200)
        self.assertIn("gaby", response_admin.data.decode("utf-8"))
        
        # 4. Obter o ID do usuário comum do banco para aprovar
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'gaby'")
        user_id = cursor.fetchone()[0]
        conn.close()
        
        # 5. Aprovar o usuário 'gaby' como administrador (POST /admin/aprovar/<id>)
        response_approve = self.client.post(f"/admin/aprovar/{user_id}", follow_redirects=True)
        self.assertIn("aprovada com sucesso!", response_approve.data.decode("utf-8"))
        
        # 6. Deslogar admin
        self.client.get("/logout")
        
        # 7. Tentar logar como 'gaby' (agora deve funcionar!)
        response_login_comum = self.client.post("/login", data={
            "username": "gaby",
            "password": "senha321"
        }, follow_redirects=True)
        
        # Deve logar com sucesso e cair na Home (200 OK)
        self.assertEqual(response_login_comum.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("username"), "gaby")
            self.assertFalse(sess.get("is_admin"))

    def test_admin_flow_promocao_e_rebaixamento(self):
        # 1. Registrar e aprovar usuário comum 'pedro'
        criar_usuario("pedro", "senha456")
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, is_admin FROM users WHERE username = 'pedro'")
        user_id, is_admin = cursor.fetchone()
        self.assertEqual(is_admin, 0)
        
        # Aprovar para permitir testes de rotas
        cursor.execute("UPDATE users SET approved = 1 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        # 2. Logar como administrador
        self.client.post("/login", data={
            "username": "vinicius",
            "password": "Vi@250793l"
        }, follow_redirects=True)
        
        # 3. Promover 'pedro' a administrador
        response_promote = self.client.post(f"/admin/toggle-admin/{user_id}", follow_redirects=True)
        self.assertIn("alterados com sucesso para Administrador!", response_promote.data.decode("utf-8"))
        
        # Validar alteração no banco
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        self.assertEqual(cursor.fetchone()[0], 1)
        conn.close()
        
        # 4. Rebaixar 'pedro' de volta para Usuário Comum
        response_demote = self.client.post(f"/admin/toggle-admin/{user_id}", follow_redirects=True)
        self.assertIn("alterados com sucesso para Usuário Comum!", response_demote.data.decode("utf-8"))
        
        # Validar alteração no banco
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        self.assertEqual(cursor.fetchone()[0], 0)
        conn.close()

        # 5. Segurança: Tentar remover seus próprios privilégios de admin deve falhar
        # (O admin logado 'vinicius' tem ID 1)
        response_self = self.client.post("/admin/toggle-admin/1", follow_redirects=True)
        self.assertIn("Você não pode alterar os seus próprios privilégios administrativos.", response_self.data.decode("utf-8"))

if __name__ == "__main__":
    unittest.main()
