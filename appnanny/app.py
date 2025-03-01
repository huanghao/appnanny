#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AppNanny: A service that manages multiple apps (Streamlit, Voila, etc.)
"""

from flask import Flask, render_template

from app_controller import app_controller, init_controller
from app_service import AppService
from logging_config import logger
from config import active_config as config


def create_app():
    app = Flask(__name__)

    # Create AppService instance and initialize controller with it
    app_service = AppService(config.STORAGE_PATH)
    init_controller(app_service)

    # Register blueprint after initializing controller
    app.register_blueprint(app_controller)

    @app.route("/")
    def index():
        return render_template("main.html")

    @app.route("/create")
    def create():
        return render_template("create.html")

    return app


if __name__ == "__main__":
    app = create_app()
    logger.info(f"Starting Flask server on {config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
