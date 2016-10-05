from flask import current_app
from ...models import AnalyticView, Location
from ... import db
import datetime as dt
import pandas as pd
import os


class ReportGenerator(object):

    def __init__(self, plz, type, year, report_id):
        self.location = Location.query.filter_by(plz=plz).first()

        self.file_name = os.path.join(current_app.config['REPORT_DIR'], 'Report_{}.xls'.format(report_id))
        self.writer = pd.ExcelWriter(self.file_name, engine='xlsxwriter')

        self.workbook = self.writer.book

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
            'percent': self.workbook.add_format({'num_format': '0.00%'})
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
        self.data.loc[self.data.rooms > 6] = 6
        rooms = pd.DataFrame({
            self.location.canton: self.data.loc[self.data.rooms != 0]
                                           .groupby('rooms')
                                           .rooms.count() / len(self.data.loc[self.data.rooms != 0]),

            self.location.district: self.data.loc[(self.data.rooms != 0) &
                                                  (self.data.district_nr == self.location.district_nr)]
                                             .groupby('rooms')
                                             .rooms.count() / len(self.data.loc[(self.data.rooms != 0) &
                                                                                (self.data.district_nr == self.location.district_nr)]),

            self.location.plz: self.data.loc[(self.data.rooms != 0) &
                                             (self.data.plz == 4103)]
                                        .groupby('rooms')
                                        .rooms.count() / len(self.data.loc[(self.data.rooms != 0) &
                                                                           (self.data.plz == self.location.plz)]),
            })

        # Insert in excel
        headers = ['1-1.5', '2-2.5', '3-3.5', '4-4.5', '5-5.5', '6+']
        title = 'Aktueller Bestand an inserierten Mietwohnugen'
        index = self.write_dataframe(rooms, worksheet, 7, title, headers, self.formats['percent'])
        worksheet.write(index, 0, 'Nicht definiert')
        worksheet.write(index, 1, self.data.loc[self.data.rooms == 0].count().rooms)


        # Design the bar plot
        fig, ax = plt.subplots()
        ax.set_xlabel('Room', rotation=0)
        ax.set_ylabel("Percent", rotation=90)
        (rooms*100).plot(kind='bar', color=['dodgerblue', 'red', 'gray'], legend=True, ax=ax)
        patches, labels = ax.get_legend_handles_labels()
        ax.legend(patches, labels, loc='best')
        # Insert in excel
        imagedata = BytesIO()
        plt.suptitle('Bestand an Mietwohnungen mit Benchmarks (Zimmerkategorie)', fontsize=20)
        plt.savefig(imagedata, format="png")
        imagedata.seek(0)
        worksheet.insert_image(40, 10, "", {'image_data': imagedata})

    def finish(self):
        self.workbook.close()

    def write_dataframe(self, df, worksheet, index, title, headers, format):
        worksheet.write(index, 0, '{}'.format(title), self.formats['h3'])
        index += 1
        for i in range(0, len(headers)):
            worksheet.write(index, i+1, '{}'.format(headers[i]))
        index += 1
        for i in range(df.shape[1]):
            worksheet.write(index+i, 0, '{}'.format(df.keys()[i]))
            for j in range(df.shape[0]):
                worksheet.write(index+i, j+1, df[df.keys()[i]][df.index[j]], format)

        return index + df.shape[1]
