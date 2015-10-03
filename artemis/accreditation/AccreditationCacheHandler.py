from artemis.LimitedCollections import LimitedDict
from artemis.Forms import Form, SQLFormManager
from .User import *
import requests

class AccreditationCacheHandler(LimitedDict):
	def __init__(self, mem_max, initialdata=None, lifetime=3600, db_location=""):
		"""
			@brief				blocking, blocking and vblocing io mustbe changed
			@param liftime		- lifetime( second ) of a robot object before updating
			@param db_location	- 
			
		"""
		LimitedDict.__init__(self, mem_max, initialdata)
		self.lifetime 		= lifetime
		
		self.formManager		= SQLFormManager()
		self.userManager		= SqliteUserManager( db_location )
		
	def get(self, auth_nature, task):
		key = str(auth_nature) + task.netloc
		
		if (key in self) and self[key].is_alive() :
			return LimitedDict.__getitem__(self, key)
		elif auth_nature == Task.AUTH_FORM:
			form = self.formManager.get( SIG_IN_FORM, task.netloc )
			user = self.userManager.getByForm( form.id )
			values, action, method = form.fill_form( user )
			
			s= request.Session()
			r = s.post( action, values, headers=user_agent )
			r.raise_for_status()
			
			
			LimitedDict.__setitem__(self, key, r.cookies)
			return r.cookies
		elif auth_nature in {Task.AUTH_HTTP_BASIC, Task.AUTH_HTTP_DIGEST, Task.AUTH_FTP}:
			user	= self.userManager.getByNetloc(auth_nature, task.netloc)
			LimitedDict.__setitem__(self, key, user)
			return user
