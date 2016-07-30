from flask_login import UserMixin

class User(UserMixin):

	def __init__(self, username, password, email):
		self.username = username.lower()
		self.password = password
		self.email = email

	def is_authenticated():
		return True

	def is_active():
		return True

	def is_annonymous():
		return False

	def get_id(self):
		conn = connect_db()
		conn.row_factory = sqlite3.Row
		curs = conn.cursor()
		curs.execute('select username from user where email = (?)', [self.email])
		return unicode(curs.fetchone())

	def get_username(self):
		return self.username

	def add_db(self):
		curs = g.db.cursor()
		curs.execute('insert into user(username, password, email) values (?, ?, ?)', [self.username, self.password, self.email])
		g.db.commit()
