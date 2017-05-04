from flask_wtf import Form
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired

class Query(Form):
	search = StringField('')
class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class ScanPDF(Form):
	noticias=[]

class RssScrapping(Form):
	media = StringField('')