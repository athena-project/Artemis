from artemis.Cache import ARCCache, EmptyItem
from artemis.Task import Task, AuthNature
from .FormHandler import FormHandler
from .Form import Form, FormNature
from .User import SqliteUserManager
import requests
from time import time

class Item:
	def __init__(self, value, lifetime=600):
		self.value		= value
		self.lifetime	= float(lifetime)
		self.deathtime	= float(lifetime) + time()
	
	def is_alive(self):
		return self.deathtime > time()

class AccreditationCache(ARCCache):
	def __init__(self, size, db_location=""):
		"""
			@brief				blocking, blocking and vblocing io mustbe changed
			@param db_location	- 
			
		"""
		self.cache 			= ARCCache( size )
		
		self.userManager	= SqliteUserManager( db_location )
		self.formHandler	= FormHandler()
		
	def get(self, auth_nature, task):
		key = str(auth_nature) + task.netloc
		
		item = self.cache[ key ]
		if not isinstance(item, EmptyItem) and item.is_alive() :
			return item.value if isinstance(item, Item) else item
		elif auth_nature == AuthNature.form :
			user = self.userManager.getByNetloc( task.auth, task.netloc )
			form = self.formHandler.extractOne( user.url, FormNature.login )
			values, action, method = form.fill_form( user )
			
			s = requests.Session()
			r = s.post( action, values )
			r.raise_for_status()
			
			self.cache[key]	= Item( r.cookies )
			return r.cookies
		elif auth_nature in {AuthNature.http_basic, AuthNature.http_digest, 
		AuthNature.ftp}:
			user	= self.userManager.getByNetloc(auth_nature, task.netloc)
			self.cache[key] = user
			return user
