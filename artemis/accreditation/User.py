import requests
from artemis.Forms import Form
import sqlite3


class User:
	def __init__(self, id, login, password, mail, auth_nature, form_id=-1): 
		self.id			= id
		self.login		= login
		self.password	= password
		self.mail		= mail
		
		self.auth_nature= auth_nature
		self.form_id	= form_id #-1 ie noform
		
class SqliteUserManager:
	def __init__(self, db_location):
		self.conn = sqlite3.connect( db_location )
	
	def getByForm(self, form_id):
		cur = self.con.cursor()
		for row in cur.execute("SELECT * FROM users WHERE form_id = ? LIMIT 1", (form_id,) ) :
			return User( row[0], row[1], row[2], row[3], row[4], row[5])
	
	def getByNetloc(self, auth_nature, netloc):
		cur = self.con.cursor()
		for row in cur.execute("SELECT * FROM users WHERE auth_nature = ? AND netloc = ? LIMIT 1", (auth_nature, netloc,) ) :
			return User( row[0], row[1], row[2], row[3], row[4], row[5])
			
	def insert(self, users):
		cur	= self.con.cursor()
		query = "INSERT INTO users (login, password, mail, auth_nature, form_id) VALUES "
		for user in users:
			query += "(?, ?, ?, ?, ?),"
		query = query[:-1]
		
		args	= []
		for user in users : 
			args.extend( [user.login, user.password, user.mail, user.auth_nature, user.form_id] )
		args = tuple( args )
		
		self.conn.execute( query, args )
		self.con.commit()
		
		firstId = self.conn.insert_id()
		for k in range( firstId, firstId+len( records ) ):
			users[k-firstId]	= k
