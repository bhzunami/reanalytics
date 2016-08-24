#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template
from flask_assets import Environment, Bundle
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO


from config import config
import os
import sys
from celery import Celery

import logging
from logging.handlers import RotatingFileHandler

bootstrap = Bootstrap()     # Add Bootstrap
db = SQLAlchemy()           # Add SQLAlchemy
assets = Environment()      # Assets (SASS)

socketio = SocketIO()
login_manager = LoginManager()                 # Add LoginManager for login_user
login_manager.session_protection = 'strong'    # basic or none
login_manager.login_view = 'auth.login'        # prefix of blueprint name


def create_file_structure(data_dir, report_dir):
    """
    Check if the data dir exists.
    If the folder 'data' and 'report' does not exists create one.
    """
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    if not os.path.exists(os.path.join(report_dir)):
        os.mkdir(report_dir)


def create_app(config_name):
    app = Flask(__name__)
    # Add config
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    app.clients = {}

    # Create data structure
    create_file_structure(app.config['DATA_DIR'], app.config['REPORT_DIR'])

    # Logging
    handler = RotatingFileHandler('reanalyticss.log', maxBytes=10000, backupCount=1)
    formatter = logging.Formatter("%(asctime)s | %(pathname)s:%(lineno)d | %(funcName)s | %(levelname)s | %(message)s ")
    # formatter = logging.Formatter( "%(asctime)s | %(funcName)s | %(levelname)s | %(message)s ")
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)

    # Init the extensions
    socketio.init_app(app)
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    # Add functionality for scss file
    assets.init_app(app)
    # paths are  to app/static/ directory.
    scss = Bundle('../scss/style.scss', filters='pyscss', output='style.css')
    try:
        assets.register('scss_all', scss)
    except Exception:
        pass

    # Configure the blueprints
    from .controller.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .controller.xml_import import xml_import as xml_import_blueprint
    app.register_blueprint(xml_import_blueprint, url_prefix='/import')

    from .controller.report import report as report_blueprint
    app.register_blueprint(report_blueprint, url_prefix='/report')

    from .controller.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app

# CELERY
def create_celery(app):
    celery = Celery('celery', include=['celery_module.tasks'])
    celery.conf.update(app.config)

    TaskBase = celery.Task

    """
    Create
    """
    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery