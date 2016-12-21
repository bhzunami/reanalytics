from flask import current_app
from ...models import AnalyticView, Location
from ... import db
import datetime as dt
import pandas as pd
import os

# To sort the index in the excel file we define a global index
sort_index = [1, 2, 3, 4, 5, 6, 0]

# We use 0...6 for the header definition to use the
# same index for every type. This is the translation
# to write in the excel
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
               5: '>= 200',
               6: 'khjggkjh'}
           }


# Group functions
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
        """Prepare a new excel file, formats and load the data from the database
        """
        self.location = Location.query.filter_by(plz=plz).first()

        # Create the filename
        self.file_name = os.path.join(current_app.config['REPORT_DIR'],
                                      'Report_{}.xls'.format(report_id))

        # Create a writer
        self.writer = pd.ExcelWriter(self.file_name,
                                     engine='xlsxwriter',
                                     options={'nan_inf_to_errors': True})

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
        # Actual data means get only ads which are at this time active -> not finished
        self.actual_data = pd.read_sql_query(
                           db.select([AnalyticView.rooms,
                                      AnalyticView.price,
                                      AnalyticView.area,
                                      AnalyticView.plz,
                                      AnalyticView.district_nr,
                                      AnalyticView.cdate,
                                      AnalyticView.edate])
                           .where(AnalyticView.canton_nr == self.location.canton_nr)
                           .where(AnalyticView.type == type)
                           # .where(AnalyticView.edate == dt.datetime.today()),
                           .where(AnalyticView.edate == "2016-07-10"),
                           db.session.bind,
                           parse_dates=['cdate', 'edate'])

        # historical data means all ads from a period of time
        self.historical_data = pd.read_sql_query(
                               db.select([AnalyticView.rooms,
                                         AnalyticView.price,
                                         AnalyticView.area,
                                         AnalyticView.plz,
                                         AnalyticView.district_nr,
                                         AnalyticView.cdate,
                                         AnalyticView.edate])
                               .where(AnalyticView.plz == self.location.plz)
                               .where(AnalyticView.type == type)
                               .where(AnalyticView.cyear >= year),
                               db.session.bind,
                               # index_col=['cdate'],
                               parse_dates=['cdate', 'edate'])

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
        """ Mengenanalyse
        """
        # Print scatterplot data
        self.write_dataframe(df=self.actual_data[(self.actual_data.price != 0) &
                             (self.actual_data.area != 0) &
                             (self.actual_data.plz == self.location.plz)]
                             [['area', 'price']].transpose(),
                             ws=self.workbook.add_worksheet('scatter_plot_data'),
                             row=1,
                             title='Data',
                             overwriteHeaders=['area', 'price'])

        # Y1
        sheetname = 'Mengenanalyse'
        worksheet = self.workbook.add_worksheet(sheetname)
        worksheet.set_row(0, 30)
        worksheet.write('A1', 'Mengenanalyse', self.formats['title'])

        # Count
        worksheet.write(1, 0, "Currently available apartments in {}".format(
            self.location.plz))
        worksheet.write(1, 1, len(self.actual_data[self.actual_data.plz == self.location.plz].index))
        worksheet.write(2, 0, "Currently available apartments in {}".format(self.location.district))
        worksheet.write(2, 1, len(self.actual_data[self.actual_data.district_nr == self.location.district_nr].index))
        worksheet.write(3, 0, "Currently available apartments in {}".format(self.location.canton))
        worksheet.write(3, 1, len(self.actual_data.index))

        # Rooms
        # - - - -
        self.actual_data['grooms'] = self.actual_data.rooms.apply(group_by_rooms)
        rooms = self.build_percent_data_frame('rooms', 'grooms')
        index = 5
        # Insert in excel
        index = self.write_dataframe(df=rooms,
                                     ws=worksheet,
                                     row=index,
                                     title='rooms',
                                     type='room',
                                     format=self.formats['percent'])

        worksheet.write(index, 0, 'Nicht definiert')
        worksheet.write(index, 1, self.actual_data.loc[self.actual_data.rooms == 0]
                        .count().rooms)

        # Price
        # - - - - -
        self.actual_data['gprice'] = self.actual_data.loc[self.actual_data.price != 0].price.apply(group_by_price)
        prices = self.build_percent_data_frame('price', 'gprice')

        # Insert in excel
        index = self.write_dataframe(df=prices,
                                     ws=worksheet,
                                     row=index+2,
                                     title='Preis',
                                     type='price',
                                     format=self.formats['percent'])

        worksheet.write(index, 0, 'Nicht definiert')
        worksheet.write(index, 1, self.actual_data.loc[self.actual_data.price == 0]
                        .count().price)

        # Area
        # - - - -
        self.actual_data['garea'] = self.actual_data.loc[self.actual_data.area != 0].area.apply(group_by_area)
        areas = self.build_percent_data_frame('area', 'garea')

        # Insert in excel
        index = self.write_dataframe(df=areas,
                                     ws=worksheet,
                                     row=index+2,
                                     title='Area',
                                     type='area',
                                     format=self.formats['percent'])
        worksheet.write(index, 0, 'Nicht definiert')
        worksheet.write(index, 1, self.actual_data.loc[self.actual_data.area == 0]
                        .count().price)
        index += 2

        # Y2
        # =======================================================================
        # Natural growth:
        # =======================================================================
        self.historical_data['grooms'] = self.historical_data.rooms.apply(group_by_rooms)
        self.historical_data['gprice'] = self.historical_data.price.apply(group_by_price)
        self.historical_data['garea'] = self.historical_data.area.apply(group_by_area)

        worksheet = self.workbook.add_worksheet('Bestandesentwicklung')
        worksheet.write(0, 0, 'Bestandesentwicklung', self.formats['h2'])
        index = 1

        # Create Timeperiod data
        cdata = self.historical_data.set_index('cdate')
        edata = self.historical_data.set_index('edate')

        # Rooms
        # - - - -
        crooms = self.make_time_series(cdata, 'grooms')
        erooms = self.make_time_series(edata, 'grooms')

        self.write_dataframe(
            df=crooms,
            ws=worksheet,
            row=index+1,
            title='Rooms new',
            type='room')

        self.write_dataframe(
            df=erooms,
            ws=worksheet,
            row=index+1,
            col=10,
            title='Room: closed',
            type='room')

        index = self.write_dataframe(
            df=crooms - erooms,
            ws=worksheet,
            row=index+1,
            col=20,
            title='Room difference',
            type='room')

        # Price
        # - - - -
        cprice = self.make_time_series(cdata, 'gprice')
        eprice = self.make_time_series(edata, 'gprice')

        self.write_dataframe(
            df=cprice,
            ws=worksheet,
            row=index+2,
            title='Price new',
            type='price')

        self.write_dataframe(
            df=eprice,
            ws=worksheet,
            row=index+2,
            col=10,
            title='Price closed',
            type='price')

        index = self.write_dataframe(
            df=cprice - eprice,
            ws=worksheet,
            row=index+2,
            col=20,
            title='Price Difference',
            type='price')

        # Area
        # - - - -
        carea = self.make_time_series(cdata, 'garea')
        earea = self.make_time_series(edata, 'garea')
        self.write_dataframe(
            df=carea,
            ws=worksheet,
            row=index+2,
            title='Area new',
            type='area')

        self.write_dataframe(
            df=earea,
            ws=worksheet,
            row=index+2,
            col=10,
            title='Area close',
            type='area')

        index = self.write_dataframe(
            df=carea - earea,
            ws=worksheet,
            row=index+2,
            col=20,
            title='Area Difference',
            type='area')

        index += 2

        # Y3
        # Durchschnittliche Wohnungsgrösse (m2)
        self.actual_data['garea'] = self.actual_data.area.apply(group_by_area)
        darea = self.actual_data.area.quantile([.25, .5, .75])
        worksheet.write(index, 0, 'Durchschnittliche Wohnungsgrösse (m2)', self.formats['h2'])
        worksheet.write(index+1, 0, '0.25')
        worksheet.write(index+1, 1, darea[0.25])
        worksheet.write(index+2, 0, '0.5')
        worksheet.write(index+2, 1, darea[0.5])
        worksheet.write(index+3, 0, '0.75')
        worksheet.write(index+3, 1, darea[0.75])

        index += 4
        quantiles = [.25, .5, .75]

        mean_area = self.build_quantile_data('area', 'grooms', quantiles)

        index = self.write_dataframe(
            df=mean_area[self.location.plz]
                    .reindex(sort_index, level=0)
                    .unstack(1),
            ws=worksheet,
            row=index+2,
            title=self.location.plz,
            type='rooms')

        index = self.write_dataframe(
            df=mean_area[self.location.district]
                    .reindex(sort_index, level=0)
                    .unstack(1),
            ws=worksheet,
            row=index+2,
            title=self.location.district,
            type='rooms')

        index = self.write_dataframe(
            df=mean_area[self.location.canton]
                    .reindex(sort_index, level=0)
                    .unstack(1),
            ws=worksheet,
            row=index+2,
            title=self.location.canton,
            type='rooms')

    # Y4
    def make_price_analysis(self):
        """ Preisanalyse
        """
        sheetname = 'Preisanalyse'
        worksheet = self.workbook.add_worksheet(sheetname)
        worksheet.set_row(0, 30)
        worksheet.write('A1', 'Preisanalyse', self.formats['title'])

        index = 2
        dprice = self.actual_data.loc[self.actual_data.price != 0].price.quantile([.25, .5, .75])
        worksheet.write(index, 0, 'Mietpreisniveau allgemein', self.formats['h2'])
        worksheet.write(index+1, 0, '0.25')
        worksheet.write(index+1, 1, dprice[0.25])
        worksheet.write(index+2, 0, '0.5')
        worksheet.write(index+2, 1, dprice[0.5])
        worksheet.write(index+3, 0, '0.75')
        worksheet.write(index+3, 1, dprice[0.75])

        index += 4
        quantiles = [.5]
        index = self.write_dataframe(
            df=self.build_quantile_data('price', 'grooms', quantiles)
                   .reindex(sort_index, level=0)
                   .unstack(1),
            ws=worksheet,
            row=index+2,
            title='Room',
            type='room')

        index = self.write_dataframe(
            df=self.build_quantile_data('price', 'garea', quantiles)
                   .reindex(sort_index, level=0)
                   .unstack(1),
            ws=worksheet,
            row=index+2,
            title='Area',
            type='area')

        # Y5
        # Price per square meter
        self.actual_data['price_per_m'] = self.actual_data.price / self.actual_data.loc[self.actual_data.area != 0].area
        index = self.write_dataframe(
            df=self.build_quantile_data('price_per_m', 'grooms', quantiles)
                   .reindex(sort_index, level=0)
                   .unstack(1),
            ws=worksheet,
            row=index+2,
            title='Price per m',
            type='room')

        # Entwicklung des Mietpreisniveaus
        self.historical_data['price_per_m'] = self.historical_data.price / self.historical_data.loc[self.historical_data.area != 0].area
        cdata = self.historical_data.set_index('cdate')
        crooms = self.make_time_seriesq(cdata, 'grooms', 'price_per_m')
        carea = self.make_time_seriesq(cdata, 'garea', 'price_per_m')
        index = self.write_dataframe(
            df=crooms,
            ws=worksheet,
            row=index+2,
            title='Preisentwicklung',
            type='room')

        index = self.write_dataframe(
            df=carea,
            ws=worksheet,
            row=index+2,
            title='Preis',
            type='area')

    # Y7
    def make_timePeriod(self):
        """
        Insertionsdauer
        """
        import numpy as np
        from datetime import date, timedelta
        twomonthago = date.today() - timedelta(60)

        self.actual_data['duration'] = self.actual_data.loc[self.actual_data.edate <= twomonthago].edate - self.actual_data.loc[self.actual_data.cdate <= twomonthago].cdate
        worksheet = self.workbook.add_worksheet('Insertionsdauer')
        worksheet.set_row(0, 30)
        worksheet.write('A1', 'Insertionsdauer', self.formats['title'])

        index = 2
        dduration = self.actual_data.duration.quantile([.25, .5, .75])
        worksheet.write(index, 0, 'Insertionsdauer', self.formats['h2'])
        worksheet.write(index+1, 0, '0.25')
        worksheet.write(index+1, 1, dduration[0.25] / (np.timedelta64(1, 'h') * 24) )
        worksheet.write(index+2, 0, '0.5')
        worksheet.write(index+2, 1, dduration[0.5]/(np.timedelta64(1, 'h') * 24))
        worksheet.write(index+3, 0, '0.75')
        worksheet.write(index+3, 1, dduration[0.75]/(np.timedelta64(1, 'h') * 24))

        index = 7
        index = self.write_dataframe(
            df=self.build_tquantile_data('duration', 'grooms', 0.5).reindex(sort_index),
            ws=worksheet,
            row=index,
            title='Room',
            type='room')

        index = self.write_dataframe(
            df=self.build_tquantile_data('duration', 'gprice', 0.5).reindex(sort_index),
            ws=worksheet,
            row=index+2,
            title='Price',
            type='price')

        index = self.write_dataframe(
            df=self.build_tquantile_data('duration', 'garea', 0.5).reindex([1, 2, 3 ,4, 5, 0]),
            ws=worksheet,
            row=index+2,
            title='Area',
            type='area')

        # Y8
        # Von 2015
        index += 2
        self.historical_data['duration'] = self.historical_data.loc[self.historical_data.edate <= twomonthago].edate - self.historical_data.loc[self.historical_data.cdate <= twomonthago].cdate

        dduration = self.historical_data.duration.quantile([.25, .5, .75])
        worksheet.write(index, 0, 'Insertionsdauer ab 2015', self.formats['h2'])
        worksheet.write(index+1, 0, '0.25')
        worksheet.write(index+1, 1, dduration[0.25] / (np.timedelta64(1, 'h') * 24))
        worksheet.write(index+2, 0, '0.5')
        worksheet.write(index+2, 1, dduration[0.5]/(np.timedelta64(1, 'h') * 24))
        worksheet.write(index+3, 0, '0.75')
        worksheet.write(index+3, 1, dduration[0.75]/(np.timedelta64(1, 'h') * 24))
        index += 3
        cdata = self.historical_data.set_index('cdate')
        crooms = self.make_time_seriesq(cdata, 'grooms', 'duration')
        cprice = self.make_time_seriesq(cdata, 'gprice', 'duration')
        carea = self.make_time_seriesq(cdata, 'garea', 'duration')
        index = self.write_dataframe(
            df=crooms,
            ws=worksheet,
            row=index+2,
            title='Entwicklung insertions dauer',
            type='room')

        index = self.write_dataframe(
            df=cprice,
            ws=worksheet,
            row=index+2,
            type='price')

        index = self.write_dataframe(
            df=carea,
            ws=worksheet,
            row=index+2,
            type='area')

    def finish(self):
        # Close the workbook
        # Write all datas to workbook just in case:
        worksheet = self.workbook.add_worksheet('actual_data')
        self.write_dataframe(df=self.actual_data.transpose(),
                             ws=worksheet,
                             overwriteHeaders=self.actual_data.keys().values.tolist())

        worksheet = self.workbook.add_worksheet('historical_data')
        self.write_dataframe(df=self.historical_data.transpose(),
                             ws=worksheet,
                             overwriteHeaders=self.historical_data.keys().values.tolist())

        self.workbook.close()

    def write_dataframe(self, df, ws, row=0, col=0, title=None, type=None, format=None, overwriteHeaders=None):
        """
        Helper method to write a dataframe to an excel worksheet
        """
        # Write title if we have a title
        if title:
            ws.write(row, col, '{}'.format(title), self.formats['h3'])
            row += 1

        # Write headers
        # Normally we would have a type and with this type we print the correct header.
        # But it is also possible to give no type and overwrite the headers
        if type:
            for i in range(0, len(df.index)):
                ws.write(row, col+i+1, headers[type][df.index[i]])
            row += 1
        # If really nessessery you can overwrite the headers
        elif overwriteHeaders:
            for i in range(0, len(overwriteHeaders)):
                ws.write(row, col+i+1, overwriteHeaders[i])
            row += 1

        # Write down the data
        for i in range(df.shape[1]):
            if isinstance(df.keys()[i], tuple):
                ws.write(row+i, col, '{}'.format(df.keys()[i][0]))
            else:
                ws.write(row+i, col, '{}'.format(df.keys()[i]))
            df[df.keys()[i]] = df[df.keys()[i]].fillna(0)
            for j in range(df.shape[0]):
                ws.write(row+i, col+j+1, df[df.keys()[i]][df.index[j]], format)

        return row + df.shape[1]

    def build_percent_data_frame(self, name, group):
        """ Build dataframe on plz/location/canton
        and calculate the percentage for this
        """
        return pd.DataFrame({
            self.location.canton:
                self.actual_data.loc[self.actual_data[name] != 0]
                    .groupby(group)[name]
                    .count() / len(self.actual_data.loc[self.actual_data[name] != 0]),

            self.location.district:
                self.actual_data.loc[(self.actual_data[name] != 0) &
                                     (self.actual_data.district_nr == self.location.district_nr)]
                    .groupby(group)[name]
                    .count() / len(self.actual_data.loc[(self.actual_data[name] != 0) &
                                                        (self.actual_data.district_nr == self.location.district_nr)]),

            self.location.plz:
                self.actual_data.loc[(self.actual_data[name] != 0) &
                                     (self.actual_data.plz == 4103)]
                    .groupby(group)[name]
                    .count() / len(self.actual_data.loc[(self.actual_data[name] != 0) &
                                                        (self.actual_data.plz == self.location.plz)])
        })

    def build_quantile_data(self, name, group, quantiles=[]):
        """Create Dataframe for plz/location/canton as key and
        calculate the quantile for the name
        If you are not dealing with timeseries use this function!

        :param name:      the attribute name you want the quantiles
        :param group:     which attribute should be grouped
        :param quantiles: a list of floats for qunatile
        """
        return pd.DataFrame({
            self.location.canton:
                self.actual_data.loc[self.actual_data[name] != 0]
                    .groupby(group)[name]
                    .quantile(quantiles),

            self.location.district:
                self.actual_data.loc[(self.actual_data[name] != 0) &
                                     (self.actual_data.district_nr == self.location.district_nr)]
                    .groupby(group)[name]
                    .quantile(quantiles),

            self.location.plz:
                self.actual_data.loc[(self.actual_data[name] != 0) &
                                     (self.actual_data.plz == self.location.plz)]
                    .groupby(group)[name]
                    .quantile(quantiles)
        })

    def build_tquantile_data(self, name, group, quantiles=[]):
        """Create Dataframe for plz/location/canton as key and
        calculate the quantile for the name
        This function deals with timeseries and for that we can not use
        the [data != 0] cause timeseries can not be used for that

        :param name:      the attribute name you want the quantiles
        :param group:     which attribute should be grouped
        :param quantiles: a list of floats for qunatile
        """
        return pd.DataFrame({
            # Canton
            self.location.canton:
                self.actual_data
                    .groupby(group)[name]
                    .quantile(quantiles),
            # District
            self.location.district:
                self.actual_data.loc[self.actual_data.district_nr == self.location.district_nr]
                    .groupby(group)[name]
                    .quantile(quantiles),
            # Plz
            self.location.plz:
                self.actual_data.loc[self.actual_data.plz == self.location.plz]
                    .groupby(group)[name]
                    .quantile(quantiles)
        })

    def make_time_series(self, df, group):
        """ Build timeseries if a timeseris is a index you can
        group with pd.TimeGrouper("M")
        """
        return df.groupby([pd.TimeGrouper("M"),
                           group])[group].count().reindex(sort_index,
                                                          level=1).unstack(0)

    def make_time_seriesq(self, df, group, attribute):
        return df.groupby([pd.TimeGrouper("M"),
                           group])[attribute].quantile(.5).reindex(sort_index,
                                                                   level=1).unstack(0)