from flask import Flask

def create_app():

    app = Flask(__name__)
    app.secret_key = "segredo-super-secreto-gabi-interface-distancia"

    # Inicializar Tabelas do Banco de Dados SQLite (CEPs e Usuários) e Seeding do Admin
    from .services.auth_services import init_user_db, seed_admin
    from .services.cep_services import init_db
    init_user_db()
    init_db()
    seed_admin()

    from .routes.main_routes import main
    from .routes.auth_routes import auth
    
    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app