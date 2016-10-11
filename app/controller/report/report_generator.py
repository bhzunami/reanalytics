from flask import current_app
from ...models import AnalyticView, Location
from ... import db
import datetime as dt
import pandas as pd
import os

colors = ['lightgreen', 'limegreen', 'greenyellow', 'darkgreen', 'yellowgreen', 'green']
#colors = ['r', 'g', 'b', 'y', 'k', 'm', 'c']
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


def header_look_up(type):


    pass


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

        # Write a scatter plot
        from io import BytesIO
        import matplotlib.pyplot as plt
        imagedata = BytesIO()
        self.data[(self.data.price != 0) & (self.data.area != 0) ].plot(kind='scatter', x='price', y='area')
        plt.suptitle('Bruttomiete & Wohnfläche {}'.format(self.location.plz), fontsize=20)
        plt.savefig(imagedata, format="png")
        imagedata.seek(0)
        worksheet.insert_image(1, 10, "", {'image_data': imagedata})
        plt.close()

        # First group sum by rooms
        # data = self.data[self.data.rooms != 0]
        # data = data[data.area != 0]
        # data = data[data.price != 0]

        # Rooms
        # - - - -
        self.data.loc[self.data.rooms > 6] = 6
        rooms = self.build_data_frame('rooms', 'rooms')

        # Insert in excel
        title = 'Aktueller Bestand an inserierten Mietwohnugen'
        index = self.write_dataframe(rooms, worksheet, 7, title, type='room', format=self.formats['percent'])
        worksheet.write(index, 0, 'Nicht definiert')
        worksheet.write(index, 1, self.data.loc[self.data.rooms == 0].count().rooms)

        # Design the bar plot
        self.write_bar_plot(df=rooms*100,
                            xlabel='Room',
                            ylabel='Percent',
                            title='Bestand an Mietwohnungen mit Benchmarks (Zimmerkategorie)',
                            xpos=40,
                            ypos=10,
                            ws=worksheet,
                            type='bar',
                            colors=colors)

        # Price
        # - - - - -
        self.data['gprice'] = self.data.loc[self.data.price != 0].price.apply(group_by_price)
        prices = self.build_data_frame('price', 'gprice')

        # Insert in excel
        index = self.write_dataframe(prices, worksheet, 14, title, type='price', format=self.formats['percent'])
        worksheet.write(index, 0, 'Nicht definiert')
        worksheet.write(index, 1, self.data.loc[self.data.price == 0].count().price)

        # Design the bar plot
        self.write_bar_plot(df=prices*100,
                            xlabel='Price',
                            ylabel='Percent',
                            title='Bestand an Mietwohnungen mit Benchmarks (Zimmerkategorie)',
                            xpos=40,
                            ypos=25,
                            ws=worksheet,
                            type='bar',
                            colors=colors)

        # Area
        # - - - -
        self.data['garea'] = self.data.loc[self.data.area != 0].area.apply(group_by_area)
        areas = self.build_data_frame('area', 'garea')

        # Insert in excel
        index = self.write_dataframe(df=areas,
                                     worksheet=worksheet,
                                     col=21,
                                     title=title,
                                     type='area',
                                     format=self.formats['percent'])
        worksheet.write(index, 0, 'Nicht definiert')
        worksheet.write(index, 1, self.data.loc[self.data.area == 0].count().price)

        # plot
        self.write_bar_plot(df=areas*100,
                            xlabel='Grösse',
                            ylabel='Percent',
                            title='Bestand an Mietwohnungen mit Benchmarks (Zimmerkategorie)',
                            xpos=40,
                            ypos=40,
                            ws=worksheet,
                            type='bar',
                            colors=colors)

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

        self.write_bar_plot(df=data.loc[data.rooms != 0].groupby(pd.TimeGrouper("M")).count().area,
                            title='Bestandsentwicklung Total',
                            xpos=75,
                            ypos=10,
                            ws=worksheet,
                            type='area',
                            colors='blue',
                            legend=False)

        index = self.write_dataframe(df=data.groupby([pd.TimeGrouper("M"), 'grooms']).rooms.count().reindex(sort_index, level=1).unstack(0),
                                     worksheet=worksheet,
                                     col=30,
                                     title='Room: Bestandsentwicklung an inserierten Mietwohnungen',
                                     type='room')

        self.write_bar_plot(df=data.groupby([pd.TimeGrouper("M"), 'grooms']).rooms.count().unstack(1),
                            title='Bestandsentwicklung rooms',
                            xpos=75,
                            ypos=25,
                            type='line',
                            ws=worksheet)

        index = self.write_dataframe(df=data.groupby([pd.TimeGrouper("M"), 'gprice']).price.count().reindex(sort_index, level=1).unstack(0),
                                     worksheet=worksheet,
                                     col=index+2,
                                     title='Price: Bestandsentwicklung an inserierten Mietwohnungen',
                                     type='price')

        self.write_bar_plot(df=data.groupby([pd.TimeGrouper("M"), 'gprice']).price.count().unstack(1),
                            title='Bestandsentwicklung Price',
                            xpos=75,
                            ypos=40,
                            type='line',
                            ws=worksheet)

        index = self.write_dataframe(df=data.groupby([pd.TimeGrouper("M"), 'garea']).area.count().reindex(sort_index, level=1).unstack(0),
                                     worksheet=worksheet,
                                     col=index+2,
                                     title='Area: Bestandsentwicklung an inserierten Mietwohnungen',
                                     type='area')

        self.write_bar_plot(df=data.groupby([pd.TimeGrouper("M"), 'garea']).area.count().unstack(1),
                            title='Bestandsentwicklung Area',
                            xpos=75,
                            ypos=55,
                            type='line',
                            ws=worksheet)

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
                                     col=index+2,
                                     title='PLZ Durchschnittliche Wohnungsgrösse (m2)',
                                     type='area')

        index = self.write_dataframe(df=mean_rooms[self.location.district].reindex(sort_index, level=0).unstack(1),
                                     worksheet=worksheet,
                                     col=index+2,
                                     title='District Durchschnittliche Wohnungsgrösse (m2)',
                                     type='area')

        index = self.write_dataframe(df=mean_rooms[self.location.canton].reindex(sort_index, level=0).unstack(1),
                                     worksheet=worksheet,
                                     col=index+2,
                                     title='Canton Durchschnittliche Wohnungsgrösse (m2)',
                                     type='area')

        self.write_bar_plot(df=mean_rooms[self.location.plz].reindex(sort_index, level=0).unstack(0),
                            title='Bestandsentwicklung Area {}'.format(self.location.plz),
                            xpos=110,
                            ypos=10,
                            type='box',
                            ws=worksheet)

        self.write_bar_plot(df=mean_rooms[self.location.district].reindex(sort_index, level=0).unstack(0),
                            title='Bestandsentwicklung Area {}'.format(self.location.district),
                            xpos=110,
                            ypos=25,
                            type='box',
                            ws=worksheet)
                        
        self.write_bar_plot(df=mean_rooms[self.location.canton].reindex(sort_index, level=0).unstack(0),
                            title='Bestandsentwicklung Area {}'.format(self.location.canton),
                            xpos=110,
                            ypos=40,
                            type='box',
                            ws=worksheet)

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
                                     col=index+2,
                                     title='PLZ Mietpreisniveau allgemein',
                                     type='price')

        index = self.write_dataframe(df=mean_prices[self.location.district].reindex(sort_index, level=0).unstack(1),
                                     worksheet=worksheet,
                                     col=index+2,
                                     title='District Mietpreisniveau allgemein',
                                     type='price')

        index = self.write_dataframe(df=mean_prices[self.location.canton].reindex(sort_index, level=0).unstack(1),
                                     worksheet=worksheet,
                                     col=index+2,
                                     title='Canton Mietpreisniveau allgemein',
                                     type='price')

        self.write_bar_plot(df=mean_prices[self.location.plz].reindex(sort_index, level=0).unstack(0),
                            title='Mietpreisniveau allgemein {}'.format(self.location.plz),
                            xpos=1,
                            ypos=10,
                            type='box',
                            ws=worksheet)

        self.write_bar_plot(df=mean_prices[self.location.district].reindex(sort_index, level=0).unstack(0),
                            title='Mietpreisniveau allgemein {}'.format(self.location.district),
                            xpos=1,
                            ypos=25,
                            type='box',
                            ws=worksheet)

        self.write_bar_plot(df=mean_prices[self.location.canton].reindex(sort_index, level=0).unstack(0),
                            title='Mietpreisniveau allgemein {}'.format(self.location.canton),
                            xpos=1,
                            ypos=40,
                            type='box',
                            ws=worksheet)

    def finish(self):
        self.workbook.close()

    def write_dataframe(self, df, worksheet, col, title=None, type=None, format=None, r=0):
        """
        Helper method to write a dataframe to an excel worksheet
        """
        if title:
            worksheet.write(col, r, '{}'.format(title), self.formats['h3'])
            col += 1
        if type:
            for i in range(0, len(df.index)):
                worksheet.write(col, i+1, headers[type][df.index[i]])
            col += 1
        for i in range(df.shape[1]):
            if r == 0:
                worksheet.write(col+i, 0, '{}'.format(df.keys()[i]))
            df[df.keys()[i]] = df[df.keys()[i]].fillna(0)
            for j in range(df.shape[0]):
                worksheet.write(col+i, j+1+r, df[df.keys()[i]][df.index[j]], format)

        return col + df.shape[1]

    def write_bar_plot(self, df, ws, xlabel=None, ylabel=None, title=None, xpos=0, ypos=0, type=None, colors=colors, legend=True):
        """
        Helper function for print bar plot in excel
        """
        from io import BytesIO
        import matplotlib.pyplot as plt
        # Design the bar plot
        fig, ax = plt.subplots()
        if xlabel:
            ax.set_xlabel(xlabel, rotation=0)
        if ylabel:
            ax.set_ylabel(ylabel, rotation=90)
        #df.plot(kind=type, color=to_rgba_array(colors[:len(df)]), legend=legend, ax=ax)
        df.plot(kind=type, legend=legend, ax=ax)
        if xlabel or ylabel:
            patches, labels = ax.get_legend_handles_labels()
            ax.legend(patches, labels, loc='best')
        # Insert in excel
        imagedata = BytesIO()
        plt.suptitle(title, fontsize=20)
        plt.savefig(imagedata, format="png")
        imagedata.seek(0)
        ws.insert_image(xpos, ypos, "", {'image_data': imagedata})
        plt.close()

    def build_data_frame(self, name, group):
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
