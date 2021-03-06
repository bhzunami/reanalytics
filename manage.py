#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# all the imports
from __future__ import absolute_import
import os
from app import create_app, create_celery, db, socketio
from app.models import User, Role, Permission, Location, Canton, District, Ad, File
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand
from flask_assets import ManageAssets

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
celery = create_celery(app)


manager = Manager(app)
migrate = Migrate(app, db)


def check_file_name(filename):
    from dateutil.parser import parse
    try:
        parse(filename)
        return True
    except ValueError:
        return False


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
    db.create_all()  # Create the materialized view

    Role.insert_roles()
    Canton.insert()
    District.insert()
    Location.insert()
    Ad.insert_initial_xml()
    User.insert_default_user()


@manager.command
def upgrade():
    from flask_migrate import upgrade
    upgrade()
    db.create_all()  # Create the materialized view


@manager.command
def import_file():
    import os
    import time
    files = [f for f in os.listdir('data') if check_file_name(os.path.splitext(f)[0])]
    print("Found {} files for import".format(len(files)))
    for file in sorted(files):
        f = File(name=file, path=os.path.abspath(os.path.join('data', file)))
        # Store file
        db.session.add(f)
        db.session.commit()

        # Import file
        print("Start import file {} with id {}".format(file, f.id))
        from celery_module.tasks import import_xml
        r = import_xml.delay(f.id, app.config['STRONGEST_SITE_ID'])
        while r.status is 'PENDING':
            print('Importing file {}'.format(f.id))
            time.sleep(5)


@manager.command
def run():
    socketio.run(app)


if __name__ == '__main__':
    manager.run()
