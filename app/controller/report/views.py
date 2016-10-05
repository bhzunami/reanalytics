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

def create_report(plz, type, year, report_id):
    """
    todo: If I have time make it clean. Ugly version
    :param plz:
    :param type:
    :param year:
    :return:
    """

    file_name = os.path.join(current_app.config['REPORT_DIR'],
                             'Report_{}.xls'.format(report_id))

    workbook = xlsxwriter.Workbook(file_name, {'nan_inf_to_errors': True})

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
            .where(AnalyticView.cyear == year),
        db.session.bind)

    # Replace all rooms which are greater as 6
    df_locality.loc[df_locality.rooms > 6] = 6
    df_locality['price_per_m'] = df_locality.price / df_locality.area.replace({ 0: 1 })
    df_locality['price_per_room'] = df_locality.price / df_locality.rooms.replace({ 0: 1 })
    # Group by room
    locality_grouped = df_locality.groupby('rooms')

    # DISTRICT
    df_districts = pd.read_sql_query(
        db.select([AnalyticView.rooms,
                   AnalyticView.price,
                   AnalyticView.area, ])
        .where(AnalyticView.district_nr == location.district_nr)
        .where(AnalyticView.type == type)
        .where(AnalyticView.cyear == year),
        db.session.bind)

    df_districts.loc[df_districts.rooms > 6] = 6
    df_districts['price_per_m'] = df_districts.price / df_districts.area.replace({0: 1})
    df_districts['price_per_room'] = df_districts.price / df_districts.rooms.replace({0: 1})
    # Group by room
    district_grouped = df_districts.groupby('rooms')

    # CANTON
    df_cantons = pd.read_sql_query(
        db.select([AnalyticView.rooms,
                   AnalyticView.price,
                   AnalyticView.area, ])
        .where(AnalyticView.canton_nr == location.canton_nr)
        .where(AnalyticView.type == type)
        .where(AnalyticView.cyear == year),
        db.session.bind)

    df_cantons.loc[df_cantons.rooms > 6] = 6
    df_cantons['price_per_m'] = df_cantons.price / df_cantons.area.replace({0: 1})
    df_cantons['price_per_room'] = df_cantons.price / df_cantons.rooms.replace({0: 1})
    # Group by room
    canton_grouped = df_cantons.groupby('rooms')

    index = 1

    # Set the first data
    #               2  A
    worksheet.write(index, 0, 'Report for {} {}'.format(plz, location.locality), h1)
    index += 1
    worksheet.write(index, 0,
                    'Im Jahr {} wurden in {} insgesamt {} Wohnungen ausgeschrieben'.format(year,
                                                                                           location.locality,
                                                                                           df_locality.rooms.count()))

    index += 1
    worksheet.write(index, 0, year)
    worksheet.write(index, 1, location.plz)
    worksheet.write(index, 2, location.locality)
    worksheet.write(index, 3, df_locality.rooms.count())

    # ======================================================
    # Anzahl
    # ======================================================

    # BENCHMARK 1
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    index += 2
    worksheet.write(index, 0, 'Benchmark 1: {} {} '.format(plz, location.locality), h3)
    data = df_locality.rooms.value_counts()
    index += 1
    for i in range(df_locality.rooms.nunique()):
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0))
        worksheet.write(index + 2, i, data.get(i, 0) / data.sum(),
                        percent)

    index += 4  # 10
    # BENCHMARK 2
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write(index, 0, 'Benchmark 2: {} '.format(location.district), h3)
    data = df_districts.rooms.value_counts()
    index += 1
    for i in range(df_districts.rooms.nunique()):
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0))
        worksheet.write(index + 2, i, data.get(i, 0) / data.sum(),
                        percent)

    index += 4  # 15
    # BENCHMARK 3
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write(index, 0, 'Benchmark 3: {} '.format(location.canton), h3)
    data = df_cantons.rooms.value_counts()
    index += 1
    for i in range(df_cantons.rooms.nunique()):
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0))
        worksheet.write(index + 2, i, data.get(i, 0) / data.sum(),
                        percent)

    #
    # ======================================================
    # Grösse m^2
    # ======================================================
    index += 4  # 20
    worksheet.write(index, 0, 'Grösse m^2', h2)
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # BENCHMARK 1
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    index += 2
    worksheet.write(index, 0, 'Benchmark 1: {} {} '.format(plz, location.locality), h3)
    data = locality_grouped.area.quantile([.25, .5, .75])
    index += 1
    for i in range(df_locality.rooms.nunique()):
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0).get(0.25, 0))
        worksheet.write(index + 2, i, data.get(i, 0).get(0.5, 0))
        worksheet.write(index + 3, i, data.get(i, 0).get(0.75))

    index += 5
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # BENCHMARK 2
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write(index, 0, 'Benchmark 2: {} '.format(location.district), h3)
    data = district_grouped.area.quantile([.25, .5, .75])
    index += 1
    for i in range(df_districts.rooms.nunique()):
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0).get(0.25, 0))
        worksheet.write(index + 2, i, data.get(i, 0).get(0.5, 0))
        worksheet.write(index + 3, i, data.get(i, 0).get(0.75))

    index += 5
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # BENCHMARK 3
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write(index, 0, 'Benchmark 3: {} '.format(location.canton), h3)
    data = canton_grouped.area.quantile([.25, .5, .75])
    index += 1
    for i in range(df_cantons.rooms.nunique()):
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0).get(0.25, 0))
        worksheet.write(index + 2, i, data.get(i, 0).get(0.5, 0))
        worksheet.write(index + 3, i, data.get(i, 0).get(0.75))

    index += 5  # 40
    # ======================================================
    # PREIS PER M^2
    # ======================================================
    worksheet.write(index, 0, 'Preis pro m^2', h2)
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # BENCHMARK 1
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    index += 2
    worksheet.write(index, 0, 'Benchmark 1 {} {}'.format(plz, location.locality), h3)
    data = locality_grouped.price_per_m.quantile([.25, .5, .75])
    index += 1
    for i in range(df_locality.rooms.nunique()):
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0)[0.25])
        worksheet.write(index + 2, i, data.get(i, 0)[0.5])
        worksheet.write(index + 3, i, data.get(i, 0)[0.75])
        
    index += 5
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # Benchmark 2
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write(index, 0, 'Benchmark 2 {}'.format(location.district), h3)
    data = district_grouped.price_per_m.quantile([.25, .5, .75])
    index += 1
    for i in range(df_districts.rooms.nunique()):
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0)[0.25])
        worksheet.write(index + 2, i, data.get(i, 0)[0.5])
        worksheet.write(index + 3, i, data.get(i, 0)[0.75])

    index += 5
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # Benchmark 3
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write(index, 0, 'Benchmark 3 {}'.format(location.canton), h3)
    data = canton_grouped.price_per_m.quantile([.25, .5, .75])
    index += 1
    for i in range(df_cantons.rooms.nunique()):
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0)[0.25])
        worksheet.write(index + 2, i, data.get(i, 0)[0.5])
        worksheet.write(index + 3, i, data.get(i, 0)[0.75])

    index += 5
    # ======================================================
    # Preis per room
    # ======================================================
    worksheet.write(index, 0, 'Preis pro Zimmer', h2)
    index += 2  # 60
    worksheet.write(index, 0, 'Benchmark 1 {} {}'.format(plz, location.locality), h3)
    data = locality_grouped.price_per_room.quantile([.25, .5, .75])
    index += 1
    for i in range(df_locality.rooms.nunique()):
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0)[0.25])
        worksheet.write(index + 2, i, data.get(i, 0)[0.5])
        worksheet.write(index + 3, i, data.get(i, 0)[0.75])

    index += 5
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # Benchmark 2
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write(index, 0, 'Benchmark 2 {}'.format(location.district), h3)
    data = district_grouped.price_per_room.quantile([.25, .5, .75])
    index += 1
    for i in range(df_districts.rooms.nunique()):
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0)[0.25])
        worksheet.write(index + 2, i, data.get(i, 0)[0.5])
        worksheet.write(index + 3, i, data.get(i, 0)[0.75])

    index += 5
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    # Benchmark 3
    # - - - - - - - - - - - - - - - - - - - - - - - - -
    worksheet.write(index, 0, 'Benchmark 3 {}'.format(location.canton), h3)
    data = canton_grouped.price_per_room.quantile([.25, .5, .75])
    index += 1
    for i in range(df_cantons.rooms.nunique()):
        worksheet.write(index, i, i)
        worksheet.write(index + 1, i, data.get(i, 0)[0.25])
        worksheet.write(index + 2, i, data.get(i, 0)[0.5])
        worksheet.write(index + 3, i, data.get(i, 0)[0.75])

    index += 5
    # ======================================================
    # Preis pro Kategorie
    # ======================================================
    worksheet.write(index, 0, 'Preis pro Preiskategorie', h2)
    index += 2  # 80
    worksheet.write(index, 0, 'Benchmark 1 {} {}'.format(plz, location.locality), h3)
    header = ['<1000', '1000 - 1499', '1500 - 2999', '>3000']
    data = []
    data.append(df_locality[df_locality.price < 1000 ].price.quantile([.25, .5, .75]))
    data.append(df_locality[(df_locality.price > 1000) & (df_locality.price < 1500)].price.quantile([.25, .5, .75]))
    data.append(df_locality[(df_locality.price > 1500) & (df_locality.price < 3000)].price.quantile([.25, .5, .75]))
    data.append(df_locality[df_locality.price > 2999].price.quantile([.25, .5, .75]))
    index += 1
    for i in range(len(data)):
        worksheet.write(index, i, header[i])
        worksheet.write(index + 1, i, data[i][0.25])
        worksheet.write(index + 2, i, data[i][0.5])
        worksheet.write(index + 3, i, data[i][0.75])

    index += 5
    worksheet.write(index, 0, 'Benchmark 2 {}'.format(location.district), h3)
    data = []
    data.append(df_districts[df_districts.price < 1000].price.quantile([.25, .5, .75]))
    data.append(df_districts[(df_districts.price > 1000) & (df_districts.price < 1500)].price.quantile([.25, .5, .75]))
    data.append(df_districts[(df_districts.price > 1500) & (df_districts.price < 3000)].price.quantile([.25, .5, .75]))
    data.append(df_districts[df_districts.price > 2999].price.quantile([.25, .5, .75]))
    index += 1
    for i in range(len(data)):
        worksheet.write(index, i, header[i])
        worksheet.write(index + 1, i, data[i][0.25])
        worksheet.write(index + 2, i, data[i][0.5])
        worksheet.write(index + 3, i, data[i][0.75])

    index += 5
    worksheet.write(index, 0, 'Benchmark 3 {}'.format(location.canton), h3)
    data = []
    data.append(df_cantons[df_cantons.price < 1000].price.quantile([.25, .5, .75]))
    data.append(df_cantons[(df_cantons.price > 1000) & (df_cantons.price < 1500)].price.quantile([.25, .5, .75]))
    data.append(df_cantons[(df_cantons.price > 1500) & (df_cantons.price < 3000)].price.quantile([.25, .5, .75]))
    data.append(df_cantons[df_cantons.price > 2999].price.quantile([.25, .5, .75]))
    index += 1
    for i in range(len(data)):
        worksheet.write(index, i, header[i])
        worksheet.write(index + 1, i, data[i][0.25])
        worksheet.write(index + 2, i, data[i][0.5])
        worksheet.write(index + 3, i, data[i][0.75])

    workbook.close()


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
                        created=dt.datetime.today(),
                        current=int(form.current.data))
        db.session.add(report)
        db.session.commit()

        rg = ReportGenerator(form.plz.data, 'Wohnung', 2016, report.id)
        rg.make_title_sheet()
        rg.make_quantitive_analysis()
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
