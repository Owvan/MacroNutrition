import os
from flask import Flask
from app.database import init_db, close_db

def create_app():
    app = Flask(__name__)
    
    # Secret Key for Sessions
    app.secret_key = os.environ.get('SECRET_KEY', 'macronutrition-teal-secret-key-2026')
    
    # Initialize SQLite database schema
    init_db()
    
    # Register Teardown DB
    app.teardown_appcontext(close_db)
    
    # Register Blueprints
    from app.routes.main_routes import main
    from app.routes.auth_routes import auth
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    
    return app
