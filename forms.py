from flask_wtf import Form 
from wtforms import StringField, BooleanField, PasswordField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo

class RegistrationForm(Form):
	username = StringField('Username', validators = [Length(max = 25), DataRequired()])
	email = StringField('Email Address', validators = [DataRequired()])
	password = PasswordField('New Password', validators = [DataRequired(), EqualTo('confirm', message = "Passwords must match."), Length(min = 6, max = 25)])
	confirm = PasswordField('Confirm Password')

class LoginForm(Form):
	username = StringField('Username', validators = [Length(max = 25), DataRequired()])
	password = PasswordField('Password', validators = [DataRequired()])
	remember_me = BooleanField('Remember Me', default = False)

class AddAssetForm(Form):
	assetname = StringField('Asset Name', validators = [Length(max = 40), DataRequired()])
	reserve_it = BooleanField('Reserve This Asset', default = False)
	days = IntegerField('Number of Days', default = 0)

class EditReservationForm(Form):
	days = IntegerField('Additional Days', default = 0)
	revoke_reservation = BooleanField('Revoke Reservation', default = False)

class MakeReservationForm(Form):
	days = IntegerField('Number of Days', default = 0, validators = [DataRequired()])

	
