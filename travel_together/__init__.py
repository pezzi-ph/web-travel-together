from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config["SECRET_KEY"] = "dev"  # change later for production
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///travel_together.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Import models so SQLAlchemy knows them
    from . import model

    # Register blueprints
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from .main import bp as main_bp
    app.register_blueprint(main_bp)

    return app


@login_manager.user_loader
def load_user(user_id):
    from .model import User
    return db.session.get(User, int(user_id))
