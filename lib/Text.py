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
from Ressource import *
import SQLFactory
import peewee
from peewee import *
import hashlib
import time


class TextManager( RessourceManager):
	def __init__(self):
		RessourceManager.__init__(self)
		self.table		= "text"
		
	
	def insert(self, record):
		cur = self.con.cursor()
		cur.execute("INSERT INTO "+self.table+" (url, domain, relatedRessources, sizes, contentTypes, times, md5, lastUpdate)"
					+"VALUES ('"+record.url+"', '"+record.domain+"', '"+record.relatedRessources+"', '"+record.sizes
					+"', '"+record.contentTypes+"', '"+record.times+"', '"+record.md5+"', '"+record.lastUpdate
					+"', '"+record.chunks+"', '"+record.revision+"')" )
		self.con.commit()
		cur.close()
		
	def update(self, record):
		cur = self.con.cursor()
		cur.execute("UPDATE urlRecord SET url:='"+record.url+"', domain:='"+record.domain+"', relatedRessources:='"+record.relatedRessources+
					"', sizes:='"+record.sizes+"', contentTypes:='"+record.contentTypes+"', times:='"+record.times+
					+"', md5:='"+record.md5+"', lastUpdate:='"+record.lastUpdate+"', chunks:='"+record.chunks
					+"', revision:='"+record.revision+"' WHERE id='"+str(record.id)+"'" )
		self.con.commit()
		cur.close()
		

class TextRecord( RessourceRecord ):
	def __init__(self, id=-1, url="", domain="", relatedRessources="", size="", contentTypes="", times="", md5="", lastUpdate="", 
	chunks="", revision=""):
		RessourceRecord.__init__(id, url, domain, relatedRessources, size, contentTypes, times, md5, chunks, lastUpdate)
		self.revision = revision


class Text( Ressource ):
	"""
	"""
	
	def __init__(self):
		Ressource.__init__(self)
		self.revision = 0 #number of revision

	def newRev(self):
		if( hashlib.md5(self.data).hexdigest() == self.md5[ self.md5.count()-1 ] ):
			pass
		else:
			pass
			#newrev c++
		

	def save(self):
		exits = False
		
		#newRev()
		#if( self.id == -1):
			#try:
				#RessourceRecord.get( RessourceRecord.url == self.url )
			#except peewee.DoesNotExists:
				#pass
			#else:
				#exists = True
		#else:
			#exists = True
		
		#if( exists ):
			#record = RessourceRecord( id			= self.id,	
								 #url				= self.url,
								 #domain				= self.domain,
								 #relatedRessources	= self.serializeTupleList(self.relatedRessources, str, int),
								 #sizes				= self.serializeSimpleList(self.sizes, int),
								 #contentTypes		= self.serializeSimpleList(self.contentTypes, str),
								 #times				= self.serializeSimpleList(self.times, int),
								 #md5				= self.serializeSimpleList(self.md5, str),
								 #chunks				= self.serializeSimpleList(self.chunks, int),
								 #lastUpdate			= self.lastUpdate,
								 #revision			= self.revision
								#)
		#else:
			#record = RessourceRecord(url			= self.url,
								 #domain				= self.domain,
								 #relatedRessources	= self.serializeTupleList(self.relatedRessources, str, int),
								 #sizes				= self.serializeSimpleList(self.sizes, int),
								 #contentTypes		= self.serializeSimpleList(self.contentTypes, str),
								 #times				= self.serializeSimpleList(self.times, int),
								 #md5				= self.serializeSimpleList(self.md5, str),
								 #chunks				= self.serializeSimpleList(self.chunks, int),
								 #lastUpdate			= self.lastUpdate,
								 #revision			= self.revision
								#)
		#record.save()

		
