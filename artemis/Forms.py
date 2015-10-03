from lxml import html
from .db.SQLFactory import getConn
from hashlib import md5


class Form:
	def __init__(self, url, body, nature, url_hash=""):
		self.url_hash	= str(url_hash if url_hash else md5(url.encode('utf-8')).hexdigest())
		self.url		= url
		self.body		= body
		self.nature		= str(nature)

class FormFactory:
	def build(raw_forms, parentTask):
		forms	= []
		
		for b,c in raw_forms:
			forms.append( Form(parentTask.url, b, c) )
		
		return forms

class SQLFormManager:
	def __init__(self, conn=None):
		"""
			@brief see Ressource.RessourceManager
		"""
		self.conn = conn if conn != None else getConn()
	
	def get(self, number, offset=0):
		cur = self.conn.cursor()
		cur.execute("SELECT * FROM forms ORDER BY id LIMIT "+number+" OFFSET "+offset)
		
		records=[]
		for row in cur: 
			r=TextRecord( row[1], row[2], row[3], row[0] )
			records.append( r )
		cur.close()
		
		return records

	def save(self, records):		
		with self.conn.cursor() as cur:
			cur.executemany("INSERT INTO form ( url_hash, url, body, nature)"+ #key : hash md5(url) ?
						"VALUES (%s, %s, %s, %s)ON DUPLICATE KEY UPDATE url=VALUES(url), body=VALUES(body), nature=VALUES(nature)",
						[ (record.url_hash, record.url, record.body, record.nature ) for record in records])
			
			self.conn.commit()

class SigInForm:
	def __init__(self, url, body, nature, id_users="l"):
		self.url		= url
		self.body		= body
		self.nature		= nature
		self.id_users	= id_users
	
	def addUser(self, user):
		self.id_users.append( user.id ) 
		
	def pick_fields(self, form_html):
		"""Return the most likely field names for username and password"""
		userfield = passfield = emailfield = None
		for x in form_html.inputs:
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
		form_html	= html.document_fromstring(body, base_url= self.url).xpath('//form')
		userfield, passfield = self.pick_fields( form_html )

		if userfield is None:
			raise Exception("No fields found that look like userfield")

		if passfield is None:
			raise Exception("No fields found that look like passfield")

		form_html.fields[userfield] = user.login
		form_html.fields[passfield] = user.password
		values = form_html.form_values() #+ self.submit_value( form_html )

		return values, form_html.action or form_html.base_url, form_html.method	
