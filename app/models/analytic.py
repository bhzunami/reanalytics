from sqlalchemy.ext.hybrid import hybrid_property

from .. import db
from . import Ad, Location, Time

from .view_factory import View, create_view


class AnalyticView(View):

    created = db.aliased(Time)
    ended = db.aliased(Time)
    __table__ = create_view("analytic_apartment_v",
                            db.select([Ad.id.label('id'),
                                      Ad.title.label('title'),
                                      Ad.type.label('type'),
                                      Ad.area.label('area'),
                                      Ad.price.label('price'),
                                      db.cast(db.cast(Ad.rooms, db.Float), db.Integer).label('rooms'),
                                      Ad.site_id.label('site_id'),
                                      # Location
                                      Location.plz.label('plz'),
                                      Location.locality.label('locality'),
                                      Location.bfs_nr.label('bfs_nr'),
                                      Location.district_nr.label('district_nr'),
                                      Location.district.label('district'),
                                      Location.canton_nr.label('canton_nr'),
                                      Location.canton.label('canton'),
                                      Location.canton_code.label('canton_code'),
                                      # Time
                                      created.date.label('cdate'),
                                      created.day.label('cday'),
                                      created.month.label('cmonth'),
                                      created.year.label('cyear'),
                                      created.business_day.label('cbusiness_day'),
                                      created.quarter.label('cquarter'),

                                      ended.date.label('edate'),
                                      ended.day.label('eday'),
                                      ended.month.label('emonth'),
                                      ended.year.label('eyear'),
                                      ended.business_day.label('ebusiness_day'),
                                      ended.quarter.label('equarter'),
                                      ]
                            )
                            .select_from(
                                db.join(Ad, Location, isouter=False)
                                .join(created, Ad.created_id==created.id, isouter=False)
                                .join(ended, Ad.ended_id == ended.id, isouter=False)
                                
                            ).where(Ad.price <= 20000)
                           )

# db.Index('analytic_view_id_idx', AnalyticView.id, unique=True)
# db.Index('analytic_view_plz_idx', AnalyticView.plz, unique=False)
# db.Index('analytic_view_canton_nr_idx', AnalyticView.canton_nr, unique=False)
# db.Index('analytic_view_district_nr_idx', AnalyticView.district_nr, unique=False)
# db.Index('analytic_view_cyear_idx', AnalyticView.cyear, unique=False)
# db.Index('analytic_view_eyear_idx', AnalyticView.eyear, unique=False)
