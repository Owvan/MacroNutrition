# GabyGeo - Verificador de Cobertura e Roteirizador de Clientes

O **GabyGeo** é um Web App moderno desenvolvido em Python (Flask) e SQLite, projetado para analisar a viabilidade logística de entregas e atendimentos de clientes. O sistema geolocaliza múltiplos clientes a partir de planilhas Excel/CSV, compara a distância física em relação às filiais da empresa, otimiza trajetos terrestres reais e conta com controle de acesso de usuários.

---

## 🚀 Principais Funcionalidades

1. **Análise de Cobertura por Planilha:**
   * Upload de planilhas de clientes (`.xlsx`, `.xls`, `.csv`).
   * Geolocalização automática dos clientes via CEP utilizando cache inteligente local (SQLite) integrado às APIs **BrasilAPI** e **ViaCEP**.
   * **Correção Automatizada de CEPs:** O sistema recupera e corrige automaticamente CEPs que iniciam com "0" e foram desconfigurados pelo Excel (ex: corrigindo inteiros como `8673000` para `08673-000`), evitando falhas de pesquisa.

2. **Múltiplas Matrizes/Filiais Nomeadas:**
   * Permite cadastrar e nomear dinamicamente ilimitadas filiais físicas de atendimento (ex: *"Matriz SP"*, *"Filial Suzano"*).
   * Associa automaticamente cada cliente à filial mais próxima física e calcula a distância geodésica.
   * Classifica clientes localizados a mais de **300 km** (ou raio personalizado) da filial mais próxima como **Fora de Cobertura**.

3. **Mapeamento e Linhas Conectoras:**
   * Dashboard interativo com mapa utilizando **Leaflet.js**.
   * Plota filiais (azul) e clientes (verde para "Dentro da Cobertura", vermelho para "Fora", amarelo para "Não Localizados").
   * Desenha linhas conectoras pontilhadas dinâmicas ligando cada cliente à sua respectiva filial mais próxima ao selecioná-lo.

4. **Planejador e Otimizador de Rotas:**
   * Permite traçar trajetos rodoviários reais por ruas e rodovias terrestres consumindo a API pública do **OSRM (Open Source Routing Machine)**.
   * **Roteirização Inteligente (TSP):** Implementa o algoritmo do *Vizinho Mais Próximo* para ordenar a sequência de visitas do veículo, calculando a menor distância total de rodagem e o tempo estimado de viagem.
   * Suporte para montagem de rota manual digitando CEPs avulsos.

5. **Controle de Acesso de Usuários (Segurança):**
   * Sistema de cadastro de usuários com criptografia segura das senhas (`pbkdf2:sha256`).
   * Fluxo de pendência: novos usuários cadastrados precisam de **aprovação administrativa** para logar.
   * Painel de Controle de Usuários restrito para gerenciar permissões, permitindo **Promover** usuários comuns a administradores ou **Rebaixar** privilégios.
   * Proteção em nível de rota com o decorador `@admin_required` para isolamento de banco de cache e painel administrativo.

---

## 🛠️ Tecnologias Utilizadas

* **Back-end:** Python, Flask, SQLite3, Pandas, Openpyxl, Geopy (Nominatim).
* **Front-end:** HTML5, CSS3 (Glassmorphism & Micro-animações), JavaScript (ES6+), Bootstrap 5, Leaflet.js.
* **APIs de Terceiros:** BrasilAPI (v2), ViaCEP, OSRM API (Roteamento).

---

## 💻 Como Rodar o Projeto Localmente

### Pré-requisitos:
* Python 3.10 ou superior instalado.

### Passo a Passo:

1. **Clonar o Repositório:**
   ```bash
   git clone https://github.com/Owvan/GabyGeo.git
   cd GabyGeo
   ```

2. **Criar e Ativar Ambiente Virtual:**
   * **Windows:**
     ```bash
     python -m venv venv
     .\venv\Scripts\activate
     ```
   * **Linux/macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instalar Dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Iniciar a Aplicação:**
   ```bash
   python run.py
   ```

5. Acesse no seu navegador: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Credenciais do Administrador Padrão

O sistema inicializa automaticamente a conta do administrador master com os dados abaixo:
* **Usuário:** `Vinicius`
* **Senha:** `Vi@250793l`
