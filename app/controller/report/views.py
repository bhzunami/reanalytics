#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import render_template, current_app, redirect, url_for
from flask_login import current_user, login_required
import datetime
from . import report
from .forms import ReportForm
from ...models import Report, AnalyticView, Location
from ... import db
import pandas as pd
import xlsxwriter
import os

def create_report(plz, type, year):
    """
    todo: If I have time make it clean. Ugly version
    :param plz:
    :param type:
    :param year:
    :return:
    """
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
    df_locality.loc[df_locality.rooms > 6] = 6
    #df_locality.rooms[df_locality.rooms > 6] = 6

    # Set the first data
    worksheet.write('A1', 'Report for {} {}'.format(plz, location.locality), h1)

    worksheet.write('A3',
                    'Im Jahr {} wurden in {} insgesamt {} Wohnungen ausgeschriebn'.format(year,
                                                                                        location.locality,
                                                                                          df_locality.rooms.count()))

    worksheet.write('A4', year)
    worksheet.write('B4', location.plz)
    worksheet.write('C4', location.locality)
    worksheet.write('D4', df_locality.rooms.count())
    count_locality = df_locality.rooms.value_counts()

    # ======================================================
    # Anzahl
    # ======================================================
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # BENCHMARK 1
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write('A6', 'Benchmark 1: {} {} '.format(plz, location.locality), h3)
    index = 7
    for i, e in enumerate(count_locality):
        #                row   col
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, count_locality.get(i, 0))
        worksheet.write(index + 2, i, count_locality.get(i, 0) / count_locality.sum(), percent)

    # Percentage
    # count[0] / count.sum()

    # DISTRICT
    df_districts = pd.read_sql_query(
        db.select([AnalyticView.rooms,
                   AnalyticView.price,
                   AnalyticView.area, ])
            .where(AnalyticView.district_nr == location.district_nr)
            .where(AnalyticView.type == type)
            .where(AnalyticView.cyear == year)
        , db.session.bind)

    df_districts.loc[df_districts.rooms > 6] = 6

    count_district = df_districts.rooms.value_counts()
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # BENCHMARK 2
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write('A12', 'Benchmark 2: {} '.format(location.district), h3)
    index = 13
    for i, e in enumerate(count_district):
        #                row   col
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, count_district.get(i, 0))
        worksheet.write(index + 2, i, count_district.get(i, 0) / count_district.sum(), percent)

    # CANTON
    df_canton = pd.read_sql_query(
            db.select([AnalyticView.rooms,
                       AnalyticView.price,
                       AnalyticView.area,])
                .where(AnalyticView.canton_nr == location.canton_nr)
                .where(AnalyticView.type == type)
                .where(AnalyticView.cyear == year)
            , db.session.bind)

    df_canton.loc[df_canton.rooms > 6] = 6

    count_canton = df_canton.rooms.value_counts()

    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # BENCHMARK 3
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write('A18', 'Benchmark 3: {} '.format(location.canton), h3)
    index = 19
    for i, e in enumerate(count_canton):
        #                row   col
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, count_canton.get(i, 0))
        worksheet.write(index + 2, i, count_canton.get(i, 0) / count_canton.sum(), percent)

    # ======================================================
    # Grösse m^2
    # ======================================================
    worksheet.write('A25', 'Grösse m^2', h2)
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # BENCHMARK 1
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write('A27', 'Benchmark 1: {} {} '.format(plz, location.locality), h3)
    locality_grouped = df_locality.groupby('rooms')
    data = locality_grouped.area.quantile([.25, .5, .75])
    index = 28
    for i, e in enumerate(count_district):
        #                row   col
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0)[0.25])
        worksheet.write(index + 2, i, data.get(i, 0)[0.5])
        worksheet.write(index + 3, i, data.get(i, 0)[0.75])

    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # BENCHMARK 2
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write('A34', 'Benchmark 2: {} '.format(location.district), h3)
    district_grouped = df_districts.groupby('rooms')
    data = district_grouped.area.quantile([.25, .5, .75])
    index = 35
    for i, e in enumerate(count_district):
        #                row   col
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0)[0.25])
        worksheet.write(index + 2, i, data.get(i, 0)[0.5])
        worksheet.write(index + 3, i, data.get(i, 0)[0.75])

    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # BENCHMARK 3
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write('A41', 'Benchmark 3: {} '.format(location.canton), h3)
    canton_grouped = df_canton.groupby('rooms')
    data = canton_grouped.area.quantile([.25, .5, .75])
    index = 42
    for i, e in enumerate(count_district):
        #                row   col
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0)[0.25])
        worksheet.write(index + 2, i, data.get(i, 0)[0.5])
        worksheet.write(index + 3, i, data.get(i, 0)[0.75])

    # ======================================================
    # PREIS PER M^2
    # ======================================================
    worksheet.write('A47', 'Preis pro m^2', h2)
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # BENCHMARK 1
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write('A48', 'Benchmark 1 {} {}'.format(plz, location.locality), h3)
    df_locality['price_per_m'] = df_locality.price / df_locality.area
    locality_grouped = df_locality.groupby('rooms')
    data = locality_grouped.price_per_m.quantile([.25, .5, .75])
    index = 49
    for i, e in enumerate(locality_grouped):
        #                row   col
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0)[0.25])
        worksheet.write(index + 2, i, data.get(i, 0)[0.5])
        worksheet.write(index + 3, i, data.get(i, 0)[0.75])
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # Benchmark 2
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write('A55', 'Benchmark 2 {}'.format(location.district), h3)
    df_districts['price_per_m'] = df_districts.price / df_districts.area
    district_grouped = df_districts.groupby('rooms')
    data = district_grouped.price_per_m.quantile([.25, .5, .75])
    index = 56
    for i, e in enumerate(district_grouped):
        #                row   col
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0)[0.25])
        worksheet.write(index + 2, i, data.get(i, 0)[0.5])
        worksheet.write(index + 3, i, data.get(i, 0)[0.75])
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # Benchmark 3
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write('A61', 'Benchmark 3 {}'.format(location.canton), h3)
    df_canton['price_per_m'] = df_canton.price / df_canton.area
    canton_grouped = df_canton.groupby('rooms')
    data = canton_grouped.price_per_m.quantile([.25, .5, .75])
    index = 62
    for i, e in enumerate(canton_grouped):
        #                row   col
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0)[0.25])
        worksheet.write(index + 2, i, data.get(i, 0)[0.5])
        worksheet.write(index + 3, i, data.get(i, 0)[0.75])

    # ======================================================
    #
    # ======================================================
    worksheet.write('A70', 'Preis pro Zimmer', h2)
    worksheet.write('A72', 'Benchmark 1 {} {}'.format(plz, location.locality), h3)
    df_locality['price_per_room'] = df_locality.price / df_locality.rooms
    locality_grouped = df_locality.groupby('rooms')
    data = locality_grouped.price_per_room.quantile([.25, .5, .75])
    index = 73
    for i, e in enumerate(locality_grouped):
        #                row   col
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0)[0.25])
        worksheet.write(index + 2, i, data.get(i, 0)[0.5])
        worksheet.write(index + 3, i, data.get(i, 0)[0.75])





    # locationp = df.groupby('rooms')
    # p.price.quantile([.25, .5, .75])

    #import json
    #print(json.dumps(data, indent=4))

    #ads_district = AnalyticView.query.filter_by(district_nr=district_nr, type=type, cyear=year).all()
    #ads_canton = AnalyticView.query.filter_by(canton_nr=canton_nr, type=type, cyear=year).all()



@login_required
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

