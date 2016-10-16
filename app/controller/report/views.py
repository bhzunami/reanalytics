#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import render_template, current_app, send_from_directory, redirect, url_for, flash
from flask_login import login_required
import datetime as dt
from . import report
from .forms import ReportForm
from .report_generator import ReportGenerator
from ...models import Report, AnalyticView, Location
from ... import db
import pandas as pd
import xlsxwriter
import os


@report.route('/', methods=['GET'])
@login_required
def index():
    reports = Report.query.all()
    return render_template('report/main.html', reports=reports)


@report.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    current_app.logger.info("Report PAGE")

    form = ReportForm()

    if form.validate_on_submit():
        report = Report(plz=form.plz.data,
                        company_name=form.company_name.data,
                        notes=form.notes.data,
                        created=dt.datetime.today())
        db.session.add(report)
        db.session.commit()

        rg = ReportGenerator(form.plz.data, 'Wohnung', 2015, report.id)
        rg.make_title_sheet()
        rg.make_quantitive_analysis()
        rg.make_price_analysis()
        rg.make_timePeriod()
        rg.finish()

        flash('Succesfully created new report', 'success')
        return send_from_directory(current_app.config['REPORT_DIR'],
                                   'Report_{}.xls'.format(report.id),
                                   as_attachment=True)

    return render_template('report/create.html', form=form)


@report.route('/download<int:report_id>', methods=['GET'])
@login_required
def download(report_id):
    current_app.logger.info("Report PAGE")

    if not report_id:
        return redirect(url_for('.index'))

    return send_from_directory(current_app.config['REPORT_DIR'],
                               'Report_{}.xls'.format(report_id),
                               as_attachment=True)


@report.route('/<int:report_id>', methods=['GET'])
@login_required
def delete(report_id):
    current_app.logger.info("Report PAGE")

    report = Report.query.get_or_404(report_id)

    try:
        os.remove(os.path.join(current_app.config['REPORT_DIR'],
                  'Report_{}.xls'.format(report_id)))
    except Exception as e:
        current_app.logger.error("Could not delete file with id {} cause {}".format(report_id, e))

    db.session.delete(report)

    flash('Succesfully delte Report', 'success')
    return redirect(url_for('.index'))
