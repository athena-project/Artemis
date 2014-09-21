#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#	@autor Severus21
#

import SQLFactory
import peewee
from peewee import *

class RessourceRecord( Model ):
	"""
	"""
	id = peewee.PrimaryKeyField()
	url = peewee.TextField()
	domain = peewee.TextField()
	relatedRessources = peewee.TextField()
	sizes = peewee.TextField()
	contentTypes = peewee.TextField()
	times = peewee.TextField()
	md5 = peewee.TextField()
	chunks = peewee.TextField()
	lastUpdate = peewee.DateTimeField( default=datetime.datetime.now ) 

	
	class Meta:
        database = db


class Ressource( Model ):
	"""
	"""
	def __init__(self):
		self.id = -1
		self.url = ""
		self.domain = ""
		self.relatedRessources = [] # [(type, id)]
		
		self.sizes = []
		self.contentTypes = []
		self.times = []
		self.md5 = []
		
		self.chunks = []
		self.lastUpdate = 0
		
		self.data = ""
		
	def hydrate(self, record):
		#for key in record.__dict__ :
			#setattr(self, key, getattr(record, key) )
		self.id 				= record.id
		self.url				= record.url
		self.domain				= record.domain
			
		self.relatedRessources	= unserializeTupleList( record.relatedRessources )
		self.sizes				= unserialiseSimpleList( record.sizes )
		self.contentTypes		= unserialiseSimpleList( record.contentTypes )
		self.times				= unserialiseSimpleList( record.times )
		self.md5				= unserialiseSimpleList( record.md5 )
		self.chunks				= unserialiseSimpleList( record.chunks )
		
		self.lastUpdate			= record.lastUpdate
		
	def serializeSimpleList(self, l):
		s = ""
		for x in l:
			s+=str(x)+":"
		return s[0:len(s)-1]
		
	def unserialiseSimpleList(self, s, f):
		l  = []
		begin=0
		end=0
		i=0
		n=len(s)
		while i<s :
			if( s[i] == ":" ):
				end = i-1
				l.append( f(s[begin, end]) )
				begin = i+1
			i+=1
		return l
		
	def serializeTupleList(self, l):
		s = ""
		for (a,b) in l:
			s+=str(a)+"|"+str(b)+":"
		return s[0:len(s)-1]
		
	def unserializeTuple(self, s, f1, f2):
		find = False
		i=0
		n=len(s)
		while( i<s && find == False):
			if( s[i] == "|"):
				find=True
			i+=1
		
		a = s[0:i-2]
		b = s[i:]
		return( f1(a),f2(b) )
		
	def unserializeTupleList(self, s, f1, f2):
		l  = []
		tmpL = self.unserialiseSimpleList(s)
		for x in tmpL:
			l.append( self.unserializeTuple( x , f1, f2) )
		return l
	
	def getById(id):
		try:
			record = RessourceRecord.get( RessourceRecord.id = id )
			r = Ressource()
			#Decorateur ?
			r.hydrate( record ) 
		except peewee.DoesNotExists:
			return None
			
	def getByUrl(url):
		try:
			record = RessourceRecord.get( RessourceRecord.url = url )
			r = Ressource()
			#Decorateur ?
			r.hydrate( record ) 
		except peewee.DoesNotExists:
			return None
	
	def save(self):
		#save on disk
		exits = False
		
		if( self.id == -1):
			try:
				RessourceRecord.get( RessourceRecord.url = self.url )
			except peewee.DoesNotExists:
				pass
			else:
				exists = True
		else:
			exists = True
		
		if( exists ):
			record = RessourceRecord( id			= self.id,	
								 url				= self.url,
								 domain				= self.domain,
								 relatedRessources	= self.serializeTupleList(self.relatedRessources, str, int),
								 sizes				= self.serializeSimpleList(self.sizes, int),
								 contentTypes		= self.serializeSimpleList(self.contentTypes, str),
								 times				= self.serializeSimpleList(self.times, int),
								 md5				= self.serializeSimpleList(self.md5, str),
								 chunks				= self.serializeSimpleList(self.chunks, int),
								 lastUpdate			= self.lastUpdate
								)
		else:
			record = RessourceRecord(url			= self.url,
								 domain				= self.domain,
								 relatedRessources	= self.serializeSimpleList(self.relatedRessources, str, int),
								 sizes				= self.serializeSimpleList(self.sizes, int),
								 contentTypes		= self.serializeSimpleList(self.contentTypes, str),
								 times				= self.serializeSimpleList(self.times, int),
								 md5				= self.serializeSimpleList(self.md5, str),
								 chunks				= self.serializeSimpleList(self.chunks, int),
								 lastUpdate			= self.lastUpdate
								)
		record.save()
		
