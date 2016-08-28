#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import render_template, current_app, redirect, url_for
from flask_login import current_user
import datetime
from . import report
from .forms import ReportForm
from ...models import Report, AnalyticView, Location
from ... import db
import pandas as pd
import xlsxwriter
import os

def create_report(plz, type, year):

    workbook = xlsxwriter.Workbook(os.path.join(current_app.config['REPORT_DIR'],
                                                'Report_{}-{}.xls'.format(plz, datetime.date.today())),
                                   {'nan_inf_to_errors': True})

    worksheet = workbook.add_worksheet('Benchmarks')

    location = Location.query.filter_by(plz=plz).first()

    # Set style
    h1 = workbook.add_format({'bold': True, 'font_size': 18})
    h2 = workbook.add_format({'bold': True, 'font_size': 16})
    h3 = workbook.add_format({'font_size': 14})

    percent = workbook.add_format({'num_format': '0.00%'})

    # Get all plz from view
    df_locality = pd.read_sql_query(
        db.select([AnalyticView.rooms,
                   AnalyticView.price,
                   AnalyticView.area, ])
            .where(AnalyticView.plz == plz)
            .where(AnalyticView.type == type)
            .where(AnalyticView.cyear == year)
        , db.session.bind)


    # Replace all rooms which are greater as 6
    df_locality.rooms[df_locality.rooms > 6] = 6

    # Set the first data
    worksheet.write('A1', 'Report for {} {}'.format(plz, location.locality), h1)

    worksheet.write('A3',
                    'Im Jahr {} wurden in {} insgesamt {} Wohnungen ausgeschriebn'.format(year,
                                                                                        location.locality,
                                                                                          df_locality.rooms.count()))

    worksheet.write('A1', year)
    worksheet.write('A2', location.plz)
    worksheet.write('A3', location.locality)
    worksheet.write('A4', df_locality.rooms.count())
    count_locality = df_locality.rooms.value_counts()
    # BENCHMARK 1: Locality
    worksheet.write('A6', 'Benchmark 1: {} {} '.format(plz, location.locality), h3)
    index = 7
    for i, e in enumerate(count_locality):
        #                row   col
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, count_locality[i])
        worksheet.write(index + 2, i, count_locality[i] / count_locality.sum(), percent)

    # Percentage
    # count[0] / count.sum()


    df_districts = pd.read_sql_query(
        db.select([AnalyticView.rooms,
                   AnalyticView.price,
                   AnalyticView.area, ])
            .where(AnalyticView.district_nr == location.district_nr)
            .where(AnalyticView.type == type)
            .where(AnalyticView.cyear == year)
        , db.session.bind)

    df_districts.rooms[df_districts.rooms > 6] = 6

    count_district = df_districts.rooms.value_counts()
    # BENCHMARK 1: Locality
    worksheet.write('A12', 'Benchmark 2: {} '.format(location.district), h3)
    index = 13
    for i, e in enumerate(count_district):
        #                row   col
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, count_district[i])
        worksheet.write(index + 2, i, count_district[i] / count_district.sum(), percent)

        # locationp = df.groupby('rooms')
    # p.price.quantile([.25, .5, .75])

    #import json
    #print(json.dumps(data, indent=4))

    #ads_district = AnalyticView.query.filter_by(district_nr=district_nr, type=type, cyear=year).all()
    #ads_canton = AnalyticView.query.filter_by(canton_nr=canton_nr, type=type, cyear=year).all()




@report.route('/', methods=['GET', 'POST'])
def index():
    current_app.logger.info("Report PAGE")

    form = ReportForm()

    if form.validate_on_submit():
        report = Report(plz=form.plz.data,
                        company_name=form.company_name.data,
                        notes=form.notes.data,
                        created=datetime.datetime.today())

        create_report(form.plz.data, 'Wohnung', 2016)

        current_app.logger.info("Report {}".format(report))
        return redirect(url_for('.index', form=None))

    return render_template('report/main.html', form=form)

