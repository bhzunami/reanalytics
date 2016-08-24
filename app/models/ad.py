#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from .. import db
from flask_login import UserMixin
from flask import current_app
import xml.etree.ElementTree as ET


class Ad(UserMixin, db.Model):
    """
    Model class of an ad
    """
    __tablename__ = "ads"

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String)
    type = db.Column(db.String)
    area = db.Column(db.Float)
    price = db.Column(db.Float)
    rooms = db.Column(db.String)
    # category = Column(Boolean, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    created_id = db.Column(db.Integer, db.ForeignKey('times.id'))
    ended_id = db.Column(db.Integer, db.ForeignKey('times.id'))
    site_id = db.Column(db.Integer)

    created = db.relationship('Time', back_populates='ads_created', foreign_keys=[created_id], cascade='save-update')
    ended = db.relationship('Time', back_populates='ads_ended', foreign_keys=[ended_id], cascade='save-update')
    location = db.relationship('Location', back_populates='ads', cascade='save-update')

    def __repr__(self):
        return ("<Ad(id={}, title={}, type={}, area={}, price={}, rooms={}, location={}, "
                "insert_date={}, updated_date={}, site_id={})>").format(self.id,
                                                                        self.title,
                                                                        self.type,
                                                                        self.area,
                                                                        self.price,
                                                                        self.location,
                                                                        self.created,
                                                                        self.ended,
                                                                        self.rooms,
                                                                        self.site_id)

    @staticmethod
    def insert_initial_xml():
        from . import Location, Time
        import progressbar
        xml_file = 'data/initial.xml'
        tree = ET.parse(xml_file)
        root = tree.getroot()
        current_app.logger.info("Try to insert {} entries".format(len(root)))

        # Pre running dates and locations:
        # It costs a lot more when we have to check if the time entry exists and when not create on
        # so before insert the ads we create all necessary time entries
        dates = {} # Set for remove duplicates
        locations_set = set()
        for ad in root:
            dates[ad[8].text] = None
            dates[ad[9].text] = None
            locations_set.add(ad[6].text)

        # Store date in database
        for date in dates:
            d = datetime.datetime.strptime(date, "%Y-%m-%d")
            business_day = True if d.weekday() < 5 else False
            quarter = (d.month - 1) // 3 + 1
            t = Time(day=d.day, month=d.month, year=d.year, business_day=business_day,
                     quarter=quarter, date=d)
            dates[date] = t
            db.session.add(t)
        db.session.commit()
        db_locations = db.session.query(Location).filter(Location.plz.in_(locations_set)).all()
        locations = {}
        current_app.logger.info("For this import {} locations are needed".format(len(db_locations)))
        for location in db_locations:
            locations[location.plz] = location

        # Insert ads
        bar = progressbar.ProgressBar(max_value=len(root), redirect_stdout=True)
        i = 0
        current_app.logger.info("Inserting {} ads.".format(len(root)))
        not_founded_locations = set()
        for ad in root:
            # Ignore duplicates which are not from id 36
            if ad[10] and ad[11].text != current_app.config['STRONGEST_SITE_ID']:
                i += 1
                continue

            ct = dates[ad[8].text]
            et = dates[ad[9].text]

            # Get location from db => This should always return a location
            try:
                location = locations[int(ad[6].text)]
            except KeyError:
                i += 1
                not_founded_locations.add(ad[6].text)
                continue

            ad_object = Ad(id=ad[0].text,
                           title=ad[1].text,
                           type=ad[2].text,
                           area=ad[3].text.replace(',', '.'),
                           price=ad[4].text.replace(',', '.'),
                           rooms=ad[5].text.replace(',', '.'),
                           location=location,
                           created=ct,
                           ended=et,
                           site_id=ad[11].text)
            db.session.add(ad_object)
            # Update the progressbar
            i += 1
            bar.update(i)
            # Commit after 10000 entries
            if i % 10000 is 0:
                db.session.commit()
        db.session.commit()

        current_app.logger.info("These PLZ where not found in the database: {}".format(not_founded_locations))
