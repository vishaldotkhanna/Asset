import sqlite3 as db
from main import connect_db
from datetime import date, datetime, timedelta

print('Releasing assets for ' + str(date.today()))
conn = connect_db()
curs =  conn.cursor()
#curs.execute('update asset set releasedate = (?) where isreserved = 1', [str(date.today())])
curs.execute('update asset set isreserved = 0 where isreserved = 1 AND releasedate = (?)', [str(date.today())])
conn.commit()
