#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .. import db
from .. import login_manager
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from .role import Role, Permission


@login_manager.user_loader
def load_user(user_id):
    """
    This Method is for the flask login module
    """
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    websocket_id = db.Column(db.String(64))
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    created = db.Column(db.DateTime, server_default=db.func.now())
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __init__(self, **kwargs):
        """
        When a new user is created we have to set the default role.
        """
        super(User, self).__init__(**kwargs)
        if self.role is None:
            self.role = Role.query.filter_by(default=True).first()

    def set_lastlogin(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def can(self, permissions):
        """
        Check the permission of the user
        """
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        """
        Check if the user is an administrator
        """
        return self.can(Permission.ADMINISTRATOR)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def insert_default_user():
        from . import Role
        r = Role.query.filter_by(name="Administrator").first()
        u = User(email=current_app.config['DEFAULT_USER_EMAIL'],
                 name=current_app.config['DEFAULT_USER_NAME'],
                 password=current_app.config['DEFAULT_USER_PASSWORD'],
                 role=r)
        db.session.add(u)
        db.session.commit()
