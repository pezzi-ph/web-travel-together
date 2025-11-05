# __init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# 1) Create the global extensions FIRST (safe to import from model later)
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"   # endpoint name

@login_manager.user_loader
def load_user(user_id: str):
    # Import INSIDE the function to avoid circular imports at module load time
    from .model import User
    return db.session.get(User, int(user_id))

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",  # replace in production
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{app.instance_path}/travel_together.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Ensure instance folder exists
    from pathlib import Path
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # 2) Init extensions on app
    db.init_app(app)
    login_manager.init_app(app)

    # 3) Register blueprints
    from .main import bp as main_bp
    app.register_blueprint(main_bp)

    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # 4) Import models AFTER db.init_app so tables are registered
    from . import model  # noqa: F401

    return app
