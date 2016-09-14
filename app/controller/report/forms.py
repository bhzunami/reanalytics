#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask_wtf import Form
from wtforms import IntegerField, SubmitField, StringField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length


class ReportForm(Form):
    current = BooleanField('Aktuell')
    plz = IntegerField('Postleitzahl', validators=[DataRequired()])
    company_name = StringField('Company name')
    notes = TextAreaField('Notes')
    submit = SubmitField('Create Report')
