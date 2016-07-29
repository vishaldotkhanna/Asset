from flask import Flask, render_template, url_for, flash, redirect, request, session, g 
from forms import LoginForm, RegistrationForm, AddAssetForm, EditReservationForm, MakeReservationForm
import sqlite3, smtplib
from contextlib import closing
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin
from datetime import date, timedelta, datetime
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from threading import Thread
from string import capwords



#Initialization
app = Flask(__name__)

#Configuration 

SECRET_KEY = 'foobar'
DEBUG = True
DATABASE = "C:\\Python27\\asset\\asset.db"
WTF_CSRF_ENABLED = True 
SMTP_SERVER = 'smtp.gmail.com:587'
ADMIN_EMAIL = 'admin@example.com' #Put admin's email address here. 

lm = LoginManager()
lm.init_app(app)

#Initialization
app.config.from_object(__name__)

def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

def create_table():	#To set up database. We need a asset.db file to exist in the main folder. 
	with closing(connect_db()) as conn:
		with app.open_resource('schema.sql', mode = 'r') as f:
			conn.cursor().executescript(f.read())
		conn.commit()

	print('Tables created.')

def fetch_user(username):
	conn = connect_db()
	conn.row_factory = sqlite3.Row
	curs = conn.cursor()
	curs.execute('select * from user where username = (?) collate nocase', [str(username)])
	return curs.fetchone()

def fetch_asset(assetname):
	conn = connect_db()
	conn.row_factory = sqlite3.Row
	curs = conn.cursor()
	curs.execute('select * from asset where assetname = (?) collate nocase', [str(assetname)])
	return curs.fetchone()

def send_asynch(to_address, message):	#Sends email asynchrously.
	data = MIMEMultipart()
	from_address = 'noreply.server995@gmail.com'
	data['From'] = from_address
	data['To'] = to_address
	data['Subject'] = message['subject']
	data.attach(MIMEText(message['body']))
	server = smtplib.SMTP(app.config['SMTP_SERVER'])
	server.ehlo()
	server.starttls()
	server.ehlo()
	server.login('noreply.server995', 'assetmanage')
	try:
		server.sendmail(from_address, to_address, str(data))
	except:
		print('User\'s email is not valid.')
		return
	server.quit()
	print('Delivered mail to %s.' % to_address)

def send_mail(to_address, message):
	thr = Thread(target = send_asynch, args = [to_address, message])
	thr.start()


class User(UserMixin):

	def __init__(self, username, password, email):
		self.username = capwords(username)
		self.password = password
		self.email = email

	def is_authenticated():
		return True

	def is_active():
		return True
	
	def is_annonymous():
		return False

	def is_admin():
		conn = connect_db()
		conn.row_factory = sqlite3.Row
		curs = conn.cursor()
		curs.execute('select isadmin from user where username = (?) collate nocase', [self.username])
		flag = curs.fetchone()[0]
		return flag == 1


	def get_id(self):
		conn = connect_db()
		conn.row_factory = sqlite3.Row
		curs = conn.cursor()
		curs.execute('select uid from user where username = (?) collate nocase', [self.username])
		return unicode(curs.fetchone()[0])

	def get_username(self):
		return self.username

	def get_email(self):
		return self.email

	def add_db(self):
		curs = g.db.cursor()
		curs.execute('insert into user(username, password, email) values (?, ?, ?)', [self.username, self.password, self.email])
		g.db.commit()


#Views 

@app.route('/')	#Home page of the user. Shows assets currently reserved by the user.
@app.route('/index')
@login_required
def index():
	# if not (g.user is not None and hasattr(g.user, 'is_authenticated') and g.user.is_authenticated):
	# 	return redirect(url_for('login'))
	curs = g.db.cursor()
	g.db.row_factory = sqlite3.Row
	curs.execute('select * from asset where isreserved = (?) and owner = (?)', [1, g.user.get_id()])
	assets = curs.fetchall()
	return render_template('index.html', assets = assets)

@lm.user_loader
def load_user(id):
	conn = connect_db()
	conn.row_factory = sqlite3.Row
	curs = conn.cursor()
	curs.execute('select * from user where uid = (?)', [id])
	foo =  curs.fetchone()
	if foo is not None:
		return User(foo[1], foo[2], foo[3])
	else:
		return 'User not found.'

@app.route('/login', methods = ['GET', 'POST'])	#Log in user.
def login():
	if g.user is not None and hasattr(g.user, 'is_authenticated') and g.user.is_authenticated:
	  	return redirect(url_for('index'))		
	form = LoginForm()
	if request.method == 'POST' and form.validate_on_submit():
		#session['remember_me'] = form.remember_me.data
		g.username = form.username.data
		g.password = form.password.data
		user_db = fetch_user(g.username)
		if user_db is not None:
			if g.password == user_db[2]:
				user = User(user_db[1], user_db[2], user_db[3])
				login_user(user, remember = form.remember_me.data)
				#g.user = user
				flash('Login successful. Welcome %s!' % user_db[1])
				return redirect(url_for('index'))
			else:
				flash('Incorrect password.')
				return redirect(url_for('login'))
		else:
			flash('No such user exists.')
			return redirect(url_for('login'))
	return render_template('login.html', title = 'Sign In', form = form)

def check_email(email):	#To check if the argument email already exists in the database. Called while registering to ensure emails are not associated with multiple accounts.
	conn = g.db
	conn.row_factory = sqlite3.Row
	curs = conn.cursor()
	curs.execute('select * from user where email = (?)', [email])
	return len(curs.fetchall()) != 0


@app.route('/register', methods = ['GET', 'POST'])	#Create a new user account.
def register():
	if g.user is not None and hasattr(g.user, 'is_authenticated') and g.user.is_authenticated:
		return redirect(url_for('index'))
	form = RegistrationForm()
	if request.method == 'POST' and form.validate_on_submit():
		if fetch_user(form.username.data) is not None:
			flash('This username already exists. Please choose another one.')
			return redirect(url_for('register'))
		elif(check_email(form.email.data)):
			flash('This email is already associated with an account. Please choose another one.')
			return redirect(url_for('register'))
		user = User(username = form.username.data, password = form.password.data, email = form.email.data)
		user.add_db()
		message = {'subject': 'Thank you for registering at AssetReservation!',
			'body': 'Hi %s, you have successfully registered at AssetReservation.' % form.username.data}
		send_mail(form.email.data, message)
		flash('Registration successful! You may now login into your account.')
		return redirect(url_for('login'))
	return render_template('register.html', title = 'Sign Up', form = form)

@app.route('/logout')	#Log out user.
@login_required
def logout():
	logout_user()
	flash('Logged out.')
	return redirect(url_for('login'))

@app.route('/addasset', methods = ['GET', 'POST'])	#To create a new asset. User can reserve the new asset here itself.
@login_required
def add_asset():
	form = AddAssetForm()
	if request.method == 'POST' and form.validate_on_submit():
		if fetch_asset(form.assetname.data) is not None:
			flash('An asset with that name already exists. Please choose another name.')
			return redirect(url_for('add_asset'))
		else:
			curs = g.db.cursor()
			if form.reserve_it.data:
				release_date = str(date.today() + timedelta(days = form.days.data))
				owner = int(g.user.get_id())
				curs.execute('insert into asset(assetname, releasedate, owner, isreserved) values (?, ?, ?, ?)', [capwords(form.assetname.data), release_date, owner, 1])
				message = {'subject': 'An asset has been reserved.',
				'body': 'User %s has reserved asset %s for %d days' % (g.user.get_username(), form.assetname.data, form.days.data)}
				send_mail(g.user.get_email(), message)
				send_mail(app.config['ADMIN_EMAIL'], message)
			else:
				curs.execute('insert into asset(assetname) values (?)', [capwords(form.assetname.data)])
			g.db.commit()
			flash('Successfully created asset named %s.' % capwords(form.assetname.data))
			return render_template('add asset.html', form = form)
	return render_template('add asset.html', form = form)

@app.route('/asset/<asset_name>')	#To display asset information.
def asset(asset_name):
	asset = fetch_asset(asset_name)
	if  asset is None:
		flash('Asset not found.')
		return redirect(url_for('index'))
	curs = g.db.cursor()
	g.db.row_factory = sqlite3.Row
	curs.execute('select username from user where uid = (?)', [asset[3]])
	owner = str(curs.fetchone()[0])
	return render_template('asset.html', title = asset_name, asset = asset, owner = owner)

@app.route('/manage')	#Manage Assets page where user can reserve new assets and change reservation of current assets.
@login_required
def manage():
	curs = g.db.cursor()
	g.db.row_factory = sqlite3.Row
	curs.execute('select * from asset where isreserved = (?) and owner = (?)', [1, g.user.get_id()])
	users_assets = curs.fetchall()
	curs.execute('select * from asset where isreserved = (?) and not owner = (?)', [1, g.user.get_id()])
	others_assets = curs.fetchall()
	curs.execute('select * from asset where isreserved = 0')
	free_assets = curs.fetchall()
	return render_template('manage.html', title = 'Manage Assets', users_assets = users_assets, others_assets = others_assets, free_assets = free_assets)

@app.route('/editreservation/<asset_name>', methods = ['GET', 'POST'])	#To edit a current reservation. User can extend reservation or revoke it. 
@login_required
def edit_reservation(asset_name):
	asset = fetch_asset(asset_name)
	if asset is None:
		flash('Asset not found.')
		return redirect(url_for('manage'))
	elif not (asset[4] == 1 and asset[3] == int(g.user.get_id())):
		flash('You can\'t edit reservation for this asset.')
		return redirect(url_for('manage'))
	form = EditReservationForm()
	if request.method == 'POST' and form.validate_on_submit():
		revoke = form.revoke_reservation.data
		curs = g.db.cursor()
		if revoke:
			curs.execute('update asset set isreserved = (?) where aid = (?)', [0, asset[0]])
			g.db.commit()
			flash('Successfully revoked reservation for asset %s.' % asset[1])
			return redirect(url_for('manage'))
		elif form.days.data != 0:
			release_date = str(datetime.strptime(str(asset[2]), '%Y-%m-%d').date() + timedelta(days = form.days.data))
			curs.execute('update asset set releasedate = (?) where aid = (?)', [release_date, asset[0]])
			g.db.commit()
			flash('Successfully updated asset %s\'s release date to %s' % (asset[1], release_date))	
		return redirect(url_for('manage'))
	return render_template('edit reservation.html', date = asset[2], form = form)

@app.route('/makereservation/<asset_name>', methods = ['GET', 'POST'])	#To make a new reservation.
@login_required
def make_reservation(asset_name):
	asset = fetch_asset(asset_name)
	if asset is None:
		flash('Asset not found.')
		return redirect(url_for('manage'))
	elif asset[4] == 1:
		flash('You can\'t reserve this asset.')
		return redirect(url_for('manage'))
	form = MakeReservationForm()
	if request.method == 'POST' and form.validate_on_submit():
		if form.days.data != 0:
			curs = g.db.cursor()
			curs.execute('update asset set isreserved = (?), owner = (?), releasedate = (?) where aid = (?)', [1, int(g.user.get_id()), str(date.today() + timedelta(days = form.days.data)), asset[0]])
			g.db.commit()
			message = {'subject': 'An asset has been reserved.',
			'body': 'User %s has reserved asset %s for %d days' % (g.user.get_username(), asset_name, form.days.data)}
			send_mail(g.user.get_email(), message)
			send_mail(app.config['ADMIN_EMAIL'], message)
			flash('Successfully reserved asset %s for %d days' % (asset[1], form.days.data))
		return redirect(url_for('manage'))
	return render_template('make reservation.html', title = 'Make Reservation', asset = asset_name, form = form)

# @app.route('/admin', methods = ['GET', 'POST'])
# @login_required
# def admin():
# 	if not g.user.is_admin():
# 		flash('You need admin priviledges before you can visit this page.')
# 		return redirect(url_for('index'))
# 	return render_template('admin.html')

	
@app.errorhandler(401)
def unauthorized_error(error):
	return render_template('401.html'), 401

@app.before_request
def before_request():
	g.db = connect_db()
	g.user = current_user

@app.teardown_request
def teardown_request(error):
	if hasattr(g, 'db'):
		g.db.close()


#Running
if __name__ == '__main__':
	app.run()



