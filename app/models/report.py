#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .. import db
from flask_login import UserMixin


class Report(UserMixin, db.Model):
    """
    Model class of an report
    """
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    company_name = db.Column(db.String)
    notes = db.Column(db.String)
    created = db.Column(db.Date)
    plz = db.Column(db.Integer)

    def __repr__(self):
        return "<(Report: id {}, copany name {}, notes {} created {} plz {} )>".format(self.id,
                                                                                       self.company_name,
                                                                                       self.notes,
                                                                                       self.created,
                                                                                       self.plz)
