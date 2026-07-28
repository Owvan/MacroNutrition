import unittest
import os
import pandas as pd
import io
import sqlite3
from app.services.cep_services import clean_cep, get_cep_from_cache, save_cep_to_cache, get_cep_details
from app.services.distancia_services import calcular_distancia
from app.services.geo_services import processar_planilha_clientes, gerar_planilha_exportacao

class TestAppFlow(unittest.TestCase):
    
    def setUp(self):
        # Usar um banco de dados de teste separado para isolamento
        self.test_db_path = "ceps_cache_test.db"
        # Monkey-patch o DB_PATH para apontar para a base temporária
        import app.services.cep_services as cs
        import app.services.geo_services as gs
        import app.routes.main_routes as mr
        self.original_db_path = cs.DB_PATH
        cs.DB_PATH = self.test_db_path
        gs.DB_PATH = self.test_db_path
        mr.DB_PATH = self.test_db_path
        
    def tearDown(self):
        # Restaurar o caminho original do banco
        import app.services.cep_services as cs
        import app.services.geo_services as gs
        import app.routes.main_routes as mr
        cs.DB_PATH = self.original_db_path
        gs.DB_PATH = self.original_db_path
        mr.DB_PATH = self.original_db_path
        
        # Apagar o banco temporário de teste
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_clean_cep(self):
        self.assertEqual(clean_cep("08673-000"), "08673000")
        self.assertEqual(clean_cep(" 08673 000 "), "08673000")
        self.assertEqual(clean_cep(8673000), "08673000")  # Tratamento de inteiros (sem 0 à esquerda)
        self.assertEqual(clean_cep(8673000.0), "08673000")  # Tratamento de floats do Excel
        self.assertEqual(clean_cep("8673000.0"), "08673000")  # Tratamento de strings floats
        self.assertEqual(clean_cep("invalid-cep"), "")
        self.assertEqual(clean_cep(None), "")

    def test_distancia_calculation(self):
        # Suzano, SP (-23.5375, -46.3088)
        # Mogi das Cruzes, SP (-23.5228, -46.1889)
        coord1 = (-23.5375, -46.3088)
        coord2 = (-23.5228, -46.1889)
        
        dist = calcular_distancia(coord1, coord2)
        self.assertIsNotNone(dist)
        # A distância real entre as duas cidades é em torno de 12-14 km
        self.assertGreater(dist, 10.0)
        self.assertLess(dist, 20.0)

    def test_cache_sqlite_db(self):
        # Salvar dados no cache de teste
        save_cep_to_cache("08673000", "Suzano", "SP", -23.5375, -46.3088)
        
        # Recuperar e validar
        cached = get_cep_from_cache("08673000")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["municipio"], "Suzano")
        self.assertEqual(cached["uf"], "SP")
        self.assertEqual(cached["latitude"], -23.5375)
        self.assertEqual(cached["longitude"], -46.3088)

    def test_processar_planilha(self):
        # 1. Popular o cache temporário para os CEPs do teste (evitando bater nas APIs web nos testes unitários)
        # Matriz 1: Av. Paulista, SP (01310-100) -> (-23.5615, -46.6562)
        save_cep_to_cache("01310100", "São Paulo", "SP", -23.5615, -46.6562)
        # Matriz 2: Filial Suzano, SP (08673-000) -> (-23.5375, -46.3088)
        save_cep_to_cache("08673000", "Suzano", "SP", -23.5375, -46.3088)
        
        # Cliente 1: Mogi das Cruzes, SP (08710-000) -> (-23.5228, -46.1889)
        # Distância aproximada para Suzano (~13km - Dentro) e para São Paulo (~50km)
        # Deve escolher Suzano como a mais próxima!
        save_cep_to_cache("08710000", "Mogi das Cruzes", "SP", -23.5228, -46.1889)
        
        # Cliente 2: Rio de Janeiro (20020-010) -> (-22.9068, -43.1729)
        # Distante de ambas (~350km - Fora)
        save_cep_to_cache("20020010", "Rio de Janeiro", "RJ", -22.9068, -43.1729)
        
        # 2. Criar DataFrame e Excel fictício na memória
        data = {
            "Nome do Cliente": ["Gaby", "Vinicius"],
            "CEP Destino": ["08710-000", "20020-010"]
        }
        df = pd.DataFrame(data)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        excel_buffer.seek(0)
        
        # 3. Lista de matrizes/filiais de entrada com nomes customizados
        matrizes_input = [
            {"nome": "Matriz Principal SP", "cep": "01310-100"},
            {"nome": "Filial Suzano", "cep": "08673-000"}
        ]
        
        # 4. Chamar o processador
        res = processar_planilha_clientes(
            file_stream=excel_buffer,
            filename="teste_clientes_multi.xlsx",
            matrizes_input=matrizes_input,
            raio_limite=300.0
        )
        
        # 5. Validações de integridade
        self.assertIn("matrizes", res)
        self.assertIn("clientes", res)
        self.assertIn("resumo", res)
        
        # Validar Matrizes resolvidas
        self.assertEqual(len(res["matrizes"]), 2)
        self.assertEqual(res["matrizes"][0]["nome"], "Matriz Principal SP")
        self.assertEqual(res["matrizes"][1]["nome"], "Filial Suzano")
        
        # Validar Clientes
        clientes = res["clientes"]
        self.assertEqual(len(clientes), 2)
        
        # Cliente 1: Gaby (Mogi das Cruzes) -> Deve estar vinculada a Suzano
        self.assertEqual(clientes[0]["nome"], "Gaby")
        self.assertEqual(clientes[0]["status"], "Dentro da Cobertura")
        self.assertEqual(clientes[0]["matriz_proxima"]["nome"], "Filial Suzano")
        self.assertLess(clientes[0]["distancia"], 20.0) # Distância para Suzano é pequena
        
        # Cliente 2: Vinicius (Rio de Janeiro) -> Deve estar Fora de Cobertura
        self.assertEqual(clientes[1]["nome"], "Vinicius")
        self.assertEqual(clientes[1]["status"], "Fora de Cobertura")
        self.assertGreater(clientes[1]["distancia"], 300.0)
        
        # Validar Resumos
        resumo = res["resumo"]
        self.assertEqual(resumo["total"], 2)
        self.assertEqual(resumo["dentro"], 1)
        self.assertEqual(resumo["fora"], 1)
        self.assertEqual(resumo["total_matrizes"], 2)
        self.assertEqual(resumo["matrizes_descartadas"], 0)
        
        # 6. Validar a geração e exportação da planilha Excel correspondente
        export_buf = gerar_planilha_exportacao(res["df_resultado"])
        self.assertIsNotNone(export_buf)
        
        export_df = pd.read_excel(export_buf)
        self.assertIn("Matriz_Mais_Proxima_Nome", export_df.columns)
        self.assertIn("Matriz_Mais_Proxima_CEP", export_df.columns)
        self.assertIn("Distância_KM", export_df.columns)
        self.assertIn("Status_Cobertura", export_df.columns)
        
        self.assertEqual(export_df.iloc[0]["Matriz_Mais_Proxima_Nome"], "Filial Suzano")
        self.assertEqual(export_df.iloc[0]["Status_Cobertura"], "Dentro da Cobertura")
        self.assertEqual(export_df.iloc[1]["Status_Cobertura"], "Fora de Cobertura")

if __name__ == "__main__":
    unittest.main()
