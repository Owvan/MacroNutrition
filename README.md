# 🥗 MacroNutrition - Sistema de Controle Alimentar, Metabólico e Evolução Corporal

[![Demonstração Online](https://img.shields.io/badge/Demo%20Online-owvan.pythonanywhere.com-0d9488?style=for-the-badge&logo=pythonanywhere)](https://owvan.pythonanywhere.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-blue)](https://www.sqlite.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

O **MacroNutrition** é uma aplicação web completa desenvolvida em **Python** e **Flask** para o controle nutricional, cálculo de metabolismo basal (TMB e TDEE), gestão de macronutrientes e acompanhamento preditivo da evolução do peso corporal.

Projetado com foco em **design moderno, alta performance e suporte a dispositivos mobile (padrão iPhone 15+)**, o sistema integra tabelas nutricionais oficiais da **UNICAMP (TACO)**, **USP (TBCA)** e consulta de **Código de Barras (EAN)** via **Open Food Facts**.

---

## 🌐 Demonstração Online

Você pode testar a aplicação em produção no link:
👉 **[https://owvan.pythonanywhere.com](https://owvan.pythonanywhere.com)**

---

## 🚀 Funcionalidades Principais

### 📊 1. Dashboard de Evolução Corporal
- **Gráficos Interativos (Chart.js)**: Acompanhe a linha de tendência de peso corporal e o comparativo com a meta estabelecida.
- **Gráfico de Rosca (Nutrientes)**: Adesão diária em tempo real aos macronutrientes (Carboidratos, Proteínas e Gorduras).
- **Design Otimizado para Mobile**: Em smartphones, o resumo diário exibe barras de progresso compactas com saldo calórico restante e botão flutuante (**FAB**) para ações rápidas.

### 🥗 2. Planejador de Dieta Diário
- **Refeições Personalizáveis**: Crie e organize suas refeições diárias (Café da Manhã, Almoço, Lanche, Jantar, Ceia).
- **Busca Tripla de Alimentos**:
  1. **Tabela TACO (UNICAMP) & TBCA (USP)**: Busca instantânea em banco de dados local refinado.
  2. **Código de Barras (EAN)**: Leitura de código de barras de produtos industrializados via API Open Food Facts com busca fallback por nome.
  3. **Alimentos Personalizados**: Cadastro rápido de receitas ou produtos específicos.
- **Medidas Caseiras**: Conversão automática para porções reais (colher de sopa, xícara, unidade, fatia, concha, gramas).

### ⚡ 3. Calculadora de Taxa Metabólica Basal (TMB & TDEE)
- **Fórmula de Mifflin-St Jeor (1990)**: Equação preditiva reconhecida pela *Academy of Nutrition and Dietetics*.
- **Cálculo ao Vivo**: Atualização instantânea da TMB e do Gasto Energético Total Diário (TDEE) conforme o nível de atividade física.
- **Sugestão de Metas**: Seleção interativa de metas (Déficit para Perda de Peso, Manutenção ou Superávit para Ganho de Massa).

### 🥑 4. Distribuição de Macronutrientes
- **Presets Nutricionais**: Alternador com padrões consagrados da **OMS** (50% C / 20% P / 30% G), **Esportiva / Hipertrofia**, **Low Carb** e **Cetogênica (Keto)**.
- **Sliders Interativos**: Ajuste percentual com cálculo imediato em gramas (g) e calorias (kcal).

### 🎯 5. Perfil & Metas Preditivas da OMS
- **Cálculo do IMC**: Índice de Massa Corporal automático com destaque para o peso ideal recomendado pela Organização Mundial da Saúde.
- **Previsão de Tempo**: Defina o peso meta e o ritmo semanal (ex: 0.50 kg/semana) para calcular exatamente quantas semanas e meses levará para atingir o objetivo, informando a data prevista de conclusão.
- **Guia Educativo da OMS**: Tabela e cards mobile detalhando as faixas de IMC e seus impactos à saúde.

### 🛡️ 6. Painel Administrativo (`/admin/usuarios`)
- **Gestão de Usuários**: Visualização de contas cadastradas, estatísticas de uso e total de refeições.
- **Controle de Acesso**: Privilégios de Administrador protegidos pelo decorator `@admin_required`.
- **Ações de Suporte**: Redefinição de senhas e exclusão segura de contas com deleção em cascata (`ON DELETE CASCADE`).

---

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.10+, Flask 3.x, Jinja2
- **Banco de Dados**: SQLite3 com `PRAGMA foreign_keys = ON;` e índices de busca otimizados
- **Frontend**: HTML5, Vanilla CSS3 (Design System responsivo em tom Teal), JavaScript (ES6)
- **Framework UI**: Bootstrap 5.3 + Bootstrap Icons
- **Visualização de Dados**: Chart.js 4.4
- **Segurança**: Werkzeug Security (`generate_password_hash`, `check_password_hash`), autorização rigorosa contra **IDOR**
- **APIs Externas**: Open Food Facts API (JSON EAN Barcode lookup)

---

## ⚙️ Como Executar o Projeto Localmente

### 1. Pré-requisitos
Certifique-se de ter o **Python 3.10+** e o **Git** instalados na sua máquina.

### 2. Clonar o Repositório
```bash
git clone https://github.com/Owvan/MacroNutrition.git
cd MacroNutrition
```

### 3. Criar e Ativar o Ambiente Virtual
- **No Windows**:
```bash
python -m venv venv
.\venv\Scripts\activate
```

- **No Linux/macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 5. Executar a Aplicação
```bash
python run.py
```
Acesse a aplicação no navegador em: **`http://127.0.0.1:5000`**

---

## ☁️ Implantação e Atualização no PythonAnywhere

Para atualizar a versão em produção hospedada no PythonAnywhere:
```bash
cd ~/MacroNutrition
git pull origin main
```
Após o `git pull`, acesse a aba **Web** no PythonAnywhere e clique em **Reload**.

---

## 📁 Estrutura do Projeto

```text
MacroNutrition/
├── app/
│   ├── __init__.py           # Inicializador da aplicação Flask
│   ├── database.py           # Conexão SQLite, schemas e helpers (parse_float)
│   ├── routes/
│   │   ├── admin_routes.py   # Rotas do painel administrativo
│   │   ├── auth_routes.py    # Login, registro e controle de acesso
│   │   └── main_routes.py    # Dashboard, diário, TMB, macros e perfil
│   ├── services/
│   │   ├── admin_services.py
│   │   ├── bmr_services.py
│   │   ├── dashboard_services.py
│   │   ├── diet_services.py
│   │   ├── macro_services.py
│   │   ├── openfoodfacts_services.py
│   │   ├── profile_services.py
│   │   └── taco_services.py
│   ├── static/
│   │   ├── css/style.css     # Design System Teal & Responsividade Mobile
│   │   └── js/               # Scripts assíncronos (dieta, TMB, macros)
│   └── templates/            # Views Jinja2 (dashboard, diet, profile, etc)
├── data/
│   └── taco_foods.json       # Tabela de alimentos TACO/TBCA
├── instance/
│   └── macronutrition.db     # Banco de dados SQLite
├── run.py                    # Script principal de inicialização
├── requirements.txt          # Dependências do projeto
└── README.md                 # Documentação oficial
```

---

## 🔒 Boas Práticas de Segurança Implementadas

1. **Proteção contra IDOR (Insecure Direct Object Reference)**:
   - Validação de propriedade do usuário (`user_id == session['user_id']`) em todas as operações de modificação ou exclusão de refeições, pesos e alimentos.
2. **Encriptação de Senhas**:
   - Armazenamento em hash seguro utilizando PBKDF2/SHA256 via Werkzeug.
3. **Integridade de Banco de Dados**:
   - Execução de `PRAGMA foreign_keys = ON;` em todas as conexões SQLite, garantindo suporte a chaves estrangeiras e integridade referencial.
4. **Tratamento de Decimais**:
   - Helper `parse_float()` para conversão sanitizada de números digitados com vírgula ou ponto (ex: `70,5` -> `70.5`), evitando erros de servidor.

---

## 📄 Licença

Este projeto está sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<p align="center">
  Desenvolvido com 💚 para promover saúde, nutrição consciente e boa forma.<br>
  <strong>Acesse a versão online:</strong> <a href="https://owvan.pythonanywhere.com">https://owvan.pythonanywhere.com</a>
</p>
