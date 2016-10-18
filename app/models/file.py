#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .. import db
from flask_login import UserMixin


class File(UserMixin, db.Model):
    """
    Model class of an file
    """
    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String)
    path = db.Column(db.String)
    imported = db.Column(db.Date)
    error = db.Column(db.Boolean)
    error_message = db.Column(db.String)
    created = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return "<(File: id {}, name {}, path {} imported {} )>".format(self.id,
                                                                       self.name,
                                                                       self.path,
                                                                       self.imported)
