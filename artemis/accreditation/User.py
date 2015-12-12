import requests
from .Form import Form
import sqlite3
from time import time


class User:
	def __init__(self, id, login, password, auth_nature, 
		netloc, lifetime=1200, url=""): #config defaut apache session 20min 
		self._id		= id
		self.login		= login
		self.password	= password
		self.netloc 	= netloc

		self.lifetime	= float(lifetime)
		self.deathtime	= float(lifetime) + time()
		
		self.auth_nature= auth_nature
		self.url		= url #used only if form_auth : url where we can get the auth form
		
	def is_alive(self):
		return self.deathtime > time()
		
class SqliteUserManager:
	def __init__(self, db_location):
		self.conn = sqlite3.connect( db_location )
	
	def create(self):
		self.conn.cursor().execute("CREATE TABLE users \
		( id INTEGER PRIMARY KEY AUTOINCREMENT,\
            login VARCHAR, password VARCHAR, \
            auth_nature INTEGER, netloc VARCHAR, lifetime INTEGER, \
            url TEXT \
            )")
            #url TEXT)")
            

	def getByNetloc(self, auth_nature, netloc):
		cur = self.conn.cursor()
		for row in cur.execute("SELECT * FROM users WHERE auth_nature\
		 = ? AND netloc = ? LIMIT 1", (auth_nature, netloc,) ) :
			return User( row[0], row[1], row[2], row[3], row[4], row[5], 
			row[6])
			
	def insert(self, users):
		cur = self.conn.cursor()
		query = "INSERT INTO users (login, password, auth_nature, \
		netloc, lifetime, url) VALUES "
		for user in users:
			query += "(?, ?, ?, ?, ?, ?),"
		query = query[:-1]
		
		args	= []
		for user in users : 
			args.extend( [user.login, user.password, user.auth_nature, 
				user.netloc, user.lifetime, user.url] )

		cur.execute( query, args  )
		self.conn.commit()
		
		firstId = cur.lastrowid
		for k, user in enumerate(users):
			user = k + firstId
