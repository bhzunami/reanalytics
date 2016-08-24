#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .. import db


class Permission:
    """
    Permissions in Bit mode
    00000000 -> Anonymous User
    00000001 -> Logged in User
    00001000 -> Editor
    10000000 -> Administrator
    """
    USER = 0x01  # Normal user when logged in
    EDITOR = 0x08  # User can edit text
    ADMINISTRATOR = 0x80  # CRUD user


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        """
        Insert some roles in to the database
        Can be run:
        python main.py shell
        >> Role.insert_roles()
        Check if Roles exists in db:
        >> Role.query.all()
        """
        roles = {'User': (Permission.USER, True),
                 'Editor': (Permission.USER |
                            Permission.EDITOR, False),
                 'Administrator': (Permission.USER |
                                   Permission.EDITOR |
                                   Permission.ADMINISTRATOR, False)
                 }
        # Check if Role exists if not create else update
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()
