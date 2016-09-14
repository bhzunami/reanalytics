# materialized_view_factory.py
# example for use with Flask-SQLAlchemy

# Accompanying blog post:
# http://www.jeffwidman.com/blog/847/

# Many thanks to Mike Bayer (@zzzeek) for his help.

from sqlalchemy.ext import compiler
from sqlalchemy.schema import DDLElement
from .. import db


class CreateView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable



@compiler.compiles(CreateView)
def compileView(element, compiler, **kw):
    # Could use "CREATE OR REPLACE MATERIALIZED VIEW..."
    # but I'd rather have noisy errors
    return 'CREATE OR REPLACE VIEW %s AS %s' % (
        element.name,
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )



def create_view(name, selectable, metadata=db.metadata):
    _mt = db.MetaData() # temp metadata just for initial Table object creation
    t = db.Table(name, _mt) # the actual mat view class is bound to db.metadata
    for c in selectable.c:
        t.append_column(db.Column(c.name, c.type, primary_key=c.primary_key))

    db.event.listen(
        metadata, 'after_create',
        CreateView(name, selectable)
        )

    @db.event.listens_for(metadata, 'after_create')
    def create_indexes(target, connection, **kw):
        for idx in t.indexes:
            idx.create(connection)

    db.event.listen(
        metadata, 'before_drop',
        db.DDL('DROP VIEW IF EXISTS ' + name)
        )
    return t

class View(db.Model):
    __abstract__ = True
