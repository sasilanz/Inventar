from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import DevelopmentConfig, ProductionConfig
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models  # noqa: F401 – Models für Alembic sichtbar machen

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from app.routes import main_bp, standort_bp, ding_bp, media_bp, verleih_bp, qr_bp, stammdaten_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(standort_bp, url_prefix='/standort')
    app.register_blueprint(ding_bp, url_prefix='/ding')
    app.register_blueprint(media_bp, url_prefix='/media')
    app.register_blueprint(verleih_bp, url_prefix='/verleih')
    app.register_blueprint(qr_bp, url_prefix='/qr')
    app.register_blueprint(stammdaten_bp, url_prefix='/stammdaten')

    return app
