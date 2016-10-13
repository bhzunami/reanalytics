from flask import current_app
from ...models import AnalyticView, Location
from ... import db
import datetime as dt
import pandas as pd
import os

sort_index = [1, 2, 3, 4, 5, 6, 0]

headers = {'room': {
                0: 'not defined',
                1: '1-1.5',
                2: '2-2.5',
                3: '3-3.5',
                4: '4-4.5',
                5: '5-5.5',
                6: '6+'
            },
           'price': {
               0: 'not defined',
               1: '<1000',
               2: '1000 - 1499',
               3: '1500 - 1999',
               4: '2000 - 2499',
               5: '2500 - 3000',
               6: '>=3000'},
           'area': {
               0: 'not defined',
               1: '<50',
               2: '50 - 99',
               3: '100 - 149',
               4: '150 - 199',
               5: '>= 200'},
           }


def group_by_rooms(value):
    if value >= 6:
        return 6
    return value


def group_by_price(value):
    if value == 0:
        return 0
    if value < 1000:
        return 1
    elif value >= 1000 and value < 1500:
        return 2
    elif value >= 1500 and value < 2000:
        return 3
    elif value >= 2000 and value < 2500:
        return 4
    elif value >= 2500 and value < 3000:
        return 5
    else:
        return 6


def group_by_area(value):
    if value == 0:
        return 0
    if value < 50:
        return 1
    elif value >= 50 and value < 100:
        return 2
    elif value >= 100 and value < 150:
        return 3
    elif value >= 150 and value < 200:
        return 4
    else:
        return 5


class ReportGenerator(object):

    def __init__(self, plz, type, year, report_id):
        self.location = Location.query.filter_by(plz=plz).first()

        self.file_name = os.path.join(current_app.config['REPORT_DIR'], 'Report_{}.xls'.format(report_id))
        self.writer = pd.ExcelWriter(self.file_name, engine='xlsxwriter')

        self.workbook = self.writer.book

        # http://xlsxwriter.readthedocs.io/format.html
        self.formats = {
            'yellow_bar': self.workbook.add_format({'bg_color': '#FFFF00',
                                                    'font_color': '#000000',
                                                    'bold': True}),
            'reanalytic_clolor': self.workbook.add_format({'bg_color': '#065f69',
                                                           'font_color': '#FFFFFF',
                                                           'bold': True,
                                                           'font_size': 20,
                                                           'valign': 'vcenter'}),
            'bold': self.workbook.add_format({'bold': True}),
            'merge_format': self.workbook.add_format({'align': 'center'}),
            'title': self.workbook.add_format({'bold': True, 'font_size': 20}),
            'h1': self.workbook.add_format({'bold': True, 'font_size': 18}),
            'h2': self.workbook.add_format({'bold': True, 'font_size': 16}),
            'h3': self.workbook.add_format({'font_size': 14}),
            'percent': self.workbook.add_format({'num_format': '0.00%'}),
            }

        # Select the data from view
        self.data = pd.read_sql_query(
                    db.select([AnalyticView.rooms,
                               AnalyticView.price,
                               AnalyticView.area,
                               AnalyticView.plz,
                               AnalyticView.district_nr, ])
                    .where(AnalyticView.canton_nr == self.location.canton_nr)
                    .where(AnalyticView.type == type)
                    # .where(AnalyticView.edate == dt.datetime.today()),
                    .where(AnalyticView.edate == "2016-07-10"),
                    db.session.bind)

    def make_title_sheet(self):
        """
        Make a title sheet with some overview data
        """
        worksheet = self.workbook.add_worksheet('Kapitalübersicht')
        worksheet.set_column(0, 0, 20)
        worksheet.set_row(5, 30)
        worksheet.write('A6', 'REANALYTICS', self.formats['title'])
        worksheet.merge_range('A9:M12', 'Report für {} {}'.format(self.location.plz,
                                                                  self.location.locality),
                              self.formats['reanalytic_clolor'])

        worksheet.write('A15', 'Datum', self.formats['bold'])
        worksheet.write('B15', '{}'.format(dt.datetime.today().strftime("%d.%m.%Y")))
        worksheet.write('A16', 'Lizensiert für', self.formats['bold'])
        worksheet.write('B16', 'Linus Schenk', )
        worksheet.write('A18', 'Powered by reanalytic.ch', self.formats['bold'])

    def make_quantitive_analysis(self):
        # import matplotlib.pyplot as plt

        sheetname = 'Mengenanalyse'
        worksheet = self.workbook.add_worksheet(sheetname)
        worksheet.set_row(0, 30)
        worksheet.write('A1', 'Mengenanalyse', self.formats['title'])

        # Count
        worksheet.write(1, 0, "Currently available apartments in {}".format(self.location.plz))
        worksheet.write(1, 1, len(self.data[self.data.plz == self.location.plz].index))
        worksheet.write(2, 0, "Currently available apartments in {}".format(self.location.district))
        worksheet.write(2, 1, len(self.data[self.data.district_nr == self.location.district_nr].index))
        worksheet.write(3, 0, "Currently available apartments in {}".format(self.location.canton))
        worksheet.write(3, 1, len(self.data.index))

        # Write a scatter plot data 
        # self.data[(self.data.price != 0) & (self.data.area != 0) ]

        self.write_dataframe(df=self.data[(self.data.price != 0) & (self.data.area != 0)][['area','price']].transpose(),
                                     worksheet=self.workbook.add_worksheet('data'),
                                     row=1,
                                     title='Data')
        
        # First group sum by rooms
        # data = self.data[self.data.rooms != 0]
        # data = data[data.area != 0]
        # data = data[data.price != 0]

        # Rooms
        # - - - -
        self.data.loc[self.data.rooms > 6] = 6
        rooms = self.build_percent_data_frame('rooms', 'rooms')

        # Insert in excel
        title = 'Aktueller Bestand an inserierten Mietwohnugen'
        index = self.write_dataframe(rooms, worksheet, row=7, title=title, type='room', format=self.formats['percent'])
        worksheet.write(index, 0, 'Nicht definiert')
        worksheet.write(index, 1, self.data.loc[self.data.rooms == 0].count().rooms)

        # Price
        # - - - - -
        self.data['gprice'] = self.data.loc[self.data.price != 0].price.apply(group_by_price)
        prices = self.build_percent_data_frame('price', 'gprice')

        # Insert in excel
        index = self.write_dataframe(prices, worksheet, row=14, title=title, type='price', format=self.formats['percent'])
        worksheet.write(index, 0, 'Nicht definiert')
        worksheet.write(index, 1, self.data.loc[self.data.price == 0].count().price)

        # Area
        # - - - -
        self.data['garea'] = self.data.loc[self.data.area != 0].area.apply(group_by_area)
        areas = self.build_percent_data_frame('area', 'garea')

        # Insert in excel
        index = self.write_dataframe(df=areas,
                                     worksheet=worksheet,
                                     row=21,
                                     title=title,
                                     type='area',
                                     format=self.formats['percent'])
        worksheet.write(index, 0, 'Nicht definiert')
        worksheet.write(index, 1, self.data.loc[self.data.area == 0].count().price)

        # =======================================================================
        # Natural growth:
        # =======================================================================
        data = pd.read_sql_query(
                    db.select([AnalyticView.rooms,
                               AnalyticView.price,
                               AnalyticView.area,
                               AnalyticView.plz,
                               AnalyticView.district_nr,
                               AnalyticView.cdate, 
                               AnalyticView.edate ])
                    .where(AnalyticView.plz == self.location.plz)
                    .where(AnalyticView.type == 'Wohnung')
                    .where(AnalyticView.cyear >= "2015"),
                    db.session.bind,
                    #index_col=['cdate'],
                    parse_dates=['cdate', 'edate'])

        data['grooms'] = data.rooms.apply(group_by_rooms)
        data['gprice'] = data.price.apply(group_by_price)
        data['garea'] = data.area.apply(group_by_area)

        data = data.set_index('cdate')

        index = self.write_dataframe(df=data.groupby([pd.TimeGrouper("M"), 'grooms']).rooms.count().reindex(sort_index, level=1).unstack(0),
                                     worksheet=worksheet,
                                     row=30,
                                     title='Room: Bestandsentwicklung an inserierten Mietwohnungen',
                                     type='room')

        index = self.write_dataframe(df=data.groupby([pd.TimeGrouper("M"), 'gprice']).price.count().reindex(sort_index, level=1).unstack(0),
                                     worksheet=worksheet,
                                     row=index+2,
                                     title='Price: Bestandsentwicklung an inserierten Mietwohnungen',
                                     type='price')

        index = self.write_dataframe(df=data.groupby([pd.TimeGrouper("M"), 'garea']).area.count().reindex(sort_index, level=1).unstack(0),
                                     worksheet=worksheet,
                                     row=index+2,
                                     title='Area: Bestandsentwicklung an inserierten Mietwohnungen',
                                     type='area')



        data2 = data.set_index('edate')
        index = self.write_dataframe(df=data2.groupby([pd.TimeGrouper("M"), 'grooms']).rooms.count().reindex(sort_index, level=1).unstack(0),
                                     worksheet=worksheet,
                                     row=30,
                                     col=10,
                                     title='Room: Bestandsentwicklung an inserierten Mietwohnungen',
                                     type='room')

        a = data.groupby([pd.TimeGrouper("M"), 'grooms']).rooms.count().reindex(sort_index, level=1).unstack(0) - data2.groupby([pd.TimeGrouper("M"), 'grooms']).rooms.count().reindex(sort_index, level=1).unstack(0)
        index = self.write_dataframe(df=a,
                                     worksheet=worksheet,
                                     row=30,
                                     col=20,
                                     title='Room: Bestandsentwicklung an inserierten Mietwohnungen',
                                     type='room')

        index = self.write_dataframe(df=data2.groupby([pd.TimeGrouper("M"), 'gprice']).price.count().reindex(sort_index, level=1).unstack(0),
                                     worksheet=worksheet,
                                     row=index+5,
                                     col=10,
                                     title='Price: Bestandsentwicklung an inserierten Mietwohnungen',
                                     type='price')

        index = self.write_dataframe(df=data2.groupby([pd.TimeGrouper("M"), 'garea']).area.count().reindex(sort_index, level=1).unstack(0),
                                     worksheet=worksheet,
                                     row=index+5,
                                     col=10,
                                     title='Area: Bestandsentwicklung an inserierten Mietwohnungen',
                                     type='area')

        
                    

        # Durchschnittliche Wohnungsgrösse (m2)

        self.data['garea'] = self.data.area.apply(group_by_area)
        darea = self.data.area.quantile([.25, .5, .75])
        worksheet.write(index, 0, 'Durchschnittliche Wohnungsgrösse (m2)')
        worksheet.write(index+1, 0, '0.25')
        worksheet.write(index+1, 1, darea[0.25])
        worksheet.write(index+2, 0, '0.5')
        worksheet.write(index+2, 1, darea[0.5])
        worksheet.write(index+3, 0, '0.75')
        worksheet.write(index+3, 1, darea[0.75])

        index += 4

        quantiles = [.25, .5, .75]
        mean_rooms = pd.DataFrame({
            self.location.canton: self.data.loc[self.data.area != 0].groupby('garea').area.quantile(quantiles),
            self.location.district: self.data.loc[(self.data.area != 0) & (self.data.district_nr == self.location.district_nr)].groupby('garea').area.quantile(quantiles),
            self.location.plz: self.data.loc[(self.data.area != 0) & (self.data.plz == self.location.plz)].groupby('garea').area.quantile(quantiles)})

        index = self.write_dataframe(df=mean_rooms[self.location.plz].reindex(sort_index, level=0).unstack(1),
                                     worksheet=worksheet,
                                     row=index+2,
                                     title='PLZ Durchschnittliche Wohnungsgrösse (m2)',
                                     type='area')

        index = self.write_dataframe(df=mean_rooms[self.location.district].reindex(sort_index, level=0).unstack(1),
                                     worksheet=worksheet,
                                     row=index+2,
                                     title='District Durchschnittliche Wohnungsgrösse (m2)',
                                     type='area')

        index = self.write_dataframe(df=mean_rooms[self.location.canton].reindex(sort_index, level=0).unstack(1),
                                     worksheet=worksheet,
                                     row=index+2,
                                     title='Canton Durchschnittliche Wohnungsgrösse (m2)',
                                     type='area')

    def make_price_analysis(self):
        sheetname = 'Preisanalyse'
        worksheet = self.workbook.add_worksheet(sheetname)
        worksheet.set_row(0, 30)
        worksheet.write('A1', 'Preisanalyse', self.formats['title'])

        index = 2

        dprice = self.data.loc[self.data.price != 0].price.quantile([.25, .5, .75])
        worksheet.write(index, 0, 'Durchschnittliche Mietpreisniveau allgemein')
        worksheet.write(index+1, 0, '0.25')
        worksheet.write(index+1, 1, dprice[0.25])
        worksheet.write(index+2, 0, '0.5')
        worksheet.write(index+2, 1, dprice[0.5])
        worksheet.write(index+3, 0, '0.75')
        worksheet.write(index+3, 1, dprice[0.75])

        index += 4
        quantiles = [.25, .5, .75]
        mean_prices = pd.DataFrame({
            self.location.canton: self.data.loc[self.data.price != 0].groupby('gprice').price.quantile(quantiles),
            self.location.district: self.data.loc[(self.data.price != 0) & (self.data.district_nr == self.location.district_nr)].groupby('gprice').price.quantile(quantiles),
            self.location.plz: self.data.loc[(self.data.price != 0) & (self.data.plz == self.location.plz)].groupby('gprice').price.quantile(quantiles)})

        index = self.write_dataframe(df=mean_prices[self.location.plz].reindex(sort_index, level=0).unstack(1),
                                     worksheet=worksheet,
                                     row=index+2,
                                     title='PLZ Mietpreisniveau allgemein',
                                     type='price')

        index = self.write_dataframe(df=mean_prices[self.location.district].reindex(sort_index, level=0).unstack(1),
                                     worksheet=worksheet,
                                     row=index+2,
                                     title='District Mietpreisniveau allgemein',
                                     type='price')

        index = self.write_dataframe(df=mean_prices[self.location.canton].reindex(sort_index, level=0).unstack(1),
                                     worksheet=worksheet,
                                     row=index+2,
                                     title='Canton Mietpreisniveau allgemein',
                                     type='price')


    def finish(self):
        self.workbook.close()

    def write_dataframe(self, df, worksheet, row=0, col=0, title=None, type=None, format=None):
        """
        Helper method to write a dataframe to an excel worksheet
        """
        if title:
            worksheet.write(row, col, '{}'.format(title), self.formats['h3'])
            row += 1
        if type:
            for i in range(0, len(df.index)):
                worksheet.write(row, col+i+1, headers[type][df.index[i]])
            row += 1
        for i in range(df.shape[1]):
            worksheet.write(row+i, col, '{}'.format(df.keys()[i]))
            df[df.keys()[i]] = df[df.keys()[i]].fillna(0)
            for j in range(df.shape[0]):
                worksheet.write(row+i, col+j+1, df[df.keys()[i]][df.index[j]], format)

        return row + df.shape[1]

    def build_percent_data_frame(self, name, group):
        return pd.DataFrame({
            self.location.canton: self.data.loc[self.data[name] != 0]
                                           .groupby(group)[name]
                                           .count() / len(self.data.loc[self.data[name] != 0]),

            self.location.district: self.data.loc[(self.data[name] != 0) &
                                                  (self.data.district_nr == self.location.district_nr)]
                                             .groupby(group)[name]
                                             .count() / len(self.data.loc[(self.data[name] != 0) &
                                                                          (self.data.district_nr == self.location.district_nr)]),

            self.location.plz: self.data.loc[(self.data[name] != 0) &
                                             (self.data.plz == 4103)]
                                        .groupby(group)[name]
                                        .count() / len(self.data.loc[(self.data[name] != 0) &
                                                                     (self.data.plz == self.location.plz)])
        })
