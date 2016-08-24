from flask_wtf import Form
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired


class UploadForm(Form):
    file = FileField('XML File', validators=[ DataRequired()])
    submit = SubmitField('Upload')