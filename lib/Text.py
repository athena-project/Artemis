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
		id = cur.lastrowid
		cur.close()
		return id
		
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
		RessourceRecord.__init__(id, url, domain, relatedRessources, size, contentTypes, times, md5, lastUpdate)
		self.chunks		= chunks
		self.revision 	= int(revision)


class Text( Ressource ):
	"""
	"""
	
	def __init__(self):
		Ressource.__init__(self)
		self.chunks		= []
		self.revision  	= 0 #number of revision

	def hydrate(self, record):
		if record == None:
			return 
		
		Ressource.hydrate(self, record)
		self.chunks		= self.unserialiseSimpleList( record.chunks )
		self.revision	= record.revision()
	
	def getRecord(self):
		
		return TextRecord(
			id					= self.id
			url					= self.url
			domain				= self.domain
			
			relatedRessources	= self.serializeTupleList( self.relatedRessources )
			sizes				= self.serializeSimpleList( self.sizes )
			contentTypes		= self.serializeSimpleList( self.contentTypes )
			times				= self.serializeSimpleList( self.times )
			md5					= self.serializeSimpleList( self.md5 )
			
			lastUpdate			= self.lastUpdate
			
			chuncks				= self.serializeSimpleList( self.chunks )
			revision			= self.revision
		)
	


class TextHandler:
	def __init__(self, manager):
		RessourceHandler.__init__(self, manager)
	
	def save(self, text):
		#SQl
		id = self.manager.insert( text.getRecord() )
		
		#Data		
		if( text.data() ):
			f = open( "save/text/"+id, "w")
			f.write( text.data )
			f.close()
