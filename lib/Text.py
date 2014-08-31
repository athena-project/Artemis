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

from Ressource import Ressource
import SQLFactory
import peewee
from peewee import *
import hashlib

class TextRecord( Model ):
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
	
	revision = peewee.TextField()

	
	class Meta:
        database = db


class Text( Ressource ):
	"""
	"""
	
	def __init__(self):
		Ressource.__init__(self)
		self.revision = 0 #number of revision

	def newRev(self):
		if( hashlib.md5(self.data).hexdigest() == self.md5[ self.md5.count()-1 ] ):
			pass
		else
			#newrev c++
		

	def save(self):
		exits = False
		
		newRev()
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
								 relatedRessources	= self.serializeTupleList(self.relatedRessources),
								 sizes				= self.serializeSimpleList(self.sizes),
								 contentTypes		= self.serializeSimpleList(self.contentTypes),
								 times				= self.serializeSimpleList(self.times),
								 md5				= self.serializeSimpleList(self.md5),
								 chunks				= self.serializeSimpleList(self.chunks),
								 lastUpdate			= self.lastUpdate,
								 revision			= self.revision
								)
		else:
			record = RessourceRecord(url			= self.url,
								 domain				= self.domain,
								 relatedRessources	= self.serializeTupleList(self.relatedRessources),
								 sizes				= self.serializeSimpleList(self.sizes),
								 contentTypes		= self.serializeSimpleList(self.contentTypes),
								 times				= self.serializeSimpleList(self.times),
								 md5				= self.serializeSimpleList(self.md5),
								 chunks				= self.chunks,
								 lastUpdate			= self.lastUpdate,
								 revision			= self.revision
								)
		record.save()

		
