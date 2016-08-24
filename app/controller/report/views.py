#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import render_template, current_app, redirect, url_for
from flask_login import current_user
from . import report
from .forms import ReportForm


@report.route('/', methods=['GET', 'POST'])
def index():
    current_app.logger.info("Report PAGE")

    form = ReportForm()

    if form.validate_on_submit():
        plz = form.plz.data
        current_app.logger.info("PLZ {}".format(plz))

        return redirect(url_for('.index', form=form))

    return render_template('report/main.html', form=form)

