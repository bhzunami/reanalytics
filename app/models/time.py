#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .. import db
from flask_login import UserMixin

class Time(UserMixin, db.Model):
    __tablename__ = "times"
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    business_day = db.Column(db.Boolean, nullable=False)
    quarter = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)

    ads_created = db.relationship('Ad', back_populates='created', foreign_keys='Ad.created_id')
    ads_ended = db.relationship('Ad', back_populates='ended', foreign_keys='Ad.ended_id')

    def __repr__(self):
        return "<Time(id={}, day={}, month={}, year={}, business_day={}, quarter={}, date={})>".format(self.id,
                                                                                                       self.day,
                                                                                                       self.month,
                                                                                                       self.year,
                                                                                                       self.business_day,
                                                                                                       self.quarter,
                                                                                                       self.date)
