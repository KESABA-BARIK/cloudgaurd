"""Routes module - register all API blueprints."""

from flask import Flask
from .baseline import baseline_bp
from .evaluation import evaluation_bp
from .dashboard import dashboard_bp
from .config_routes import config_bp


def register_routes(app: Flask):
    """Register all route blueprints with the Flask app."""
    app.register_blueprint(baseline_bp)
    app.register_blueprint(evaluation_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(config_bp)


__all__ = ['register_routes']
