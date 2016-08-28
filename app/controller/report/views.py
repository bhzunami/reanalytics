#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import render_template, current_app, redirect, url_for
from flask_login import current_user
import datetime
from . import report
from .forms import ReportForm
from ...models import Report, AnalyticView


@report.route('/', methods=['GET', 'POST'])
def index():
    current_app.logger.info("Report PAGE")

    form = ReportForm()

    if form.validate_on_submit():
        report = Report(plz=form.plz.data,
                        company_name=form.company_name.data,
                        notes=form.notes.data,
                        created=datetime.datetime.today())

        current_app.logger.info("Report {}".format(report))
        return redirect(url_for('.index', form=form))

    a = AnalyticView.query.all()
    return render_template('report/main.html', form=form, a=a)

