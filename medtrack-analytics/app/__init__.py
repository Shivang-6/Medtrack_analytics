# app/__init__.py
import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# Initialize extensions
db = SQLAlchemy()
cors = CORS()


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Initialize extensions
    db.init_app(app)
    cors.init_app(app)

    # Import models to register with SQLAlchemy
    from app import models  # noqa: F401

    # Import and register blueprints
    from app.api.drug_routes import drug_bp
    from app.api.sales_routes import sales_bp
    from app.api.analytics_routes import analytics_bp
    from app.api.patient_routes import patient_bp
    from app.api.pipeline_routes import pipeline_bp

    app.register_blueprint(drug_bp, url_prefix='/api')
    app.register_blueprint(sales_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/api')
    app.register_blueprint(patient_bp, url_prefix='/api')
    app.register_blueprint(pipeline_bp, url_prefix='/api')

    # Health check
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'service': 'MedTrack Analytics API'}

    # Ensure tables exist at startup
    with app.app_context():
        db.create_all()

    return app
