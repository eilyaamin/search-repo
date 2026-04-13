"""Application factory module.

This module contains the Flask application factory function for creating
and configuring the application instance.
"""

from flask import Flask, request
from flask_cors import CORS
from src.features.repositories.routes import repo_bp
import logging

__all__ = ["create_app"]


def create_app() -> Flask:
    """Create and configure the Flask application.
    
    This factory function:
    - Initializes the Flask app
    - Configures CORS for cross-origin requests
    - Sets up logging for request/response tracking
    - Registers blueprints for all feature modules
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    CORS(app)  # allows all origins on all routes
    
    logging.basicConfig(level=logging.WARNING)


    app.register_blueprint(repo_bp, url_prefix="/api")

    return app
