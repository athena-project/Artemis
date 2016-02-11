from lxml import html
import sqlite3
from hashlib import sha224
from enum import Enum

class NoUserField(Exception):
	pass
	
class NoPassField(Exception):
	pass

class FormNature(Enum): #see Fromasaurus
	search		= "search"
	login		= "login"
	register  	= "registration"
	recovery	= "password/login recovery" 
	mail		= "join mailing list	"
	contact		= "contact/comment"
	other		= "other"

def build(url, html, nature):
	return forms[nature]( url, html, nature)
	
class Form:
	def __init__(self, id, url, body, nature):
		self.url		= url
		self.body		= body
		self.nature		= str(nature)
		self._id		= id #-1

class SigInForm:
	def __init__(self, url, body, nature, id_users="l"):
		self.url		= url
		self.body		= body
		self.nature		= nature
		self.id_users	= id_users
	
	def addUser(self, user):
		self.id_users.append( user.id ) 
		
	def pick_fields(self):
		"""Return the most likely field names for username and password"""
		userfield = passfield = emailfield = None
		for x in self.body.inputs:
			if not isinstance(x, html.InputElement):
				continue
	
			type_ = x.type
			if type_ == 'password' and passfield is None:
				passfield = x.name
			elif type_ == 'text' and userfield is None:
				userfield = x.name
			elif type_ == 'email' and emailfield is None:
				emailfield = x.name

		return userfield or emailfield, passfield
		
	#def submit_value(self, form_html):
		#"""Returns the value for the submit input, if any"""
		#for x in form_html.inputs:
			#if x.type == "submit" and x.name:
				#return [(x.name, x.value)]
		#else:
			#return []


	def fill_form(self, user):
		userfield, passfield = self.pick_fields()

		if userfield is None:
			raise NoUserField()

		if passfield is None:
			raise NoPassField()

		self.body.fields[userfield] = user.login
		self.body.fields[passfield] = user.password
		values = self.body.form_values() #+ self.submit_value( self.body )

		return( values, self.body.action 
		or self.body.base_url, self.body.method	)

forms = {
	FormNature.login : SigInForm
}
