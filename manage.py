#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# all the imports
from __future__ import absolute_import
import os
#from flask import current_app
#from celery import Celery
from app import create_app, create_celery, db, socketio
from app.models import User, Role, Permission, Location, Canton, District, Ad
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand
from flask_assets import ManageAssets

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
celery = create_celery(app)


manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    """
    Import all the stuff when run in shell
    # python main.py shell
    >> User
    <class 'app.User'>
    """
    return dict(app=app, db=db, User=User, Role=Role, Permission=Permission, Location=Location, Canton=Canton,
                District=District, Ad=Ad)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command("runserver", Server(extra_files=["app/scss/*.scss"]))
manager.add_command("assets", ManageAssets())


@manager.command
def initialize():
    from flask_migrate import upgrade
    from app.models import Role, Ad
    upgrade()

    Role.insert_roles()
    Canton.insert()
    District.insert()
    Location.insert()
    Ad.insert_initial_xml()
    User.insert_default_user()


@manager.command
def run():
    socketio.run(app)

if __name__ == '__main__':
    manager.run()
