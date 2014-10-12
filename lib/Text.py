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

import libpyRessource


class TextManager( RessourceManager):
	def __init__(self, con=None):
		RessourceManager.__init__(self, con)
		self.table		= "text"
		
	def __del__():
		RessourceManager.__del__(self)
	
	
	def getByUrl(self, url):
		cur = self.con.cursor()
		cur.execute("SELECT * FROM "+self.table+" WHERE url='"+url+"'")

		r=None
		for row in cur: #url is a unique id
			r=TextRecord( row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10] )
		cur.close()
		
		return r
	
	def insert(self, record):
		cur = self.con.cursor()
		cur.execute("INSERT INTO "+self.table+" (url, domain, relatedRessources, sizes, contentTypes, times, sha512, lastUpdate, chunks, revision)"
					+"VALUES ('"+record.url+"', '"+record.domain+"', '"+record.relatedRessources+"', '"+record.sizes
					+"', '"+record.contentTypes+"', '"+record.times+"', '"+record.sha512+"', '"+str(record.lastUpdate)
					+"', '"+record.chunks+"', '"+str(record.revision)+"')" )
		self.con.commit()
		id = cur.lastrowid
		cur.close()
		return id
	
		def insertList(self, records):
		buff = ""
		for record in records:
			if buff != "":
				buff+=", "
			buff += "('"+record.url+"', '"+record.domain+"', '"+record.relatedRessources+"', '"+record.sizes
			buff += "', '"+record.contentTypes+"', '"+record.times+"', '"+record.sha512+"', '"+str(record.lastUpdate)
			buff += "', '"+record.chunks+"', '"+str(record.revision)+"')"
		
		cur = self.con.cursor()
		cur.execute("INSERT INTO "+self.table+" (url, domain, relatedRessources, sizes, contentTypes, times, sha512, lastUpdate)"
					+"VALUES "+buff )
		self.con.commit()
		cur.close()
	
	def update(self, record):
		cur = self.con.cursor()
		cur.execute("UPDATE "+self.table+" SET url:='"+record.url+"', domain:='"+record.domain+"', relatedRessources:='"+record.relatedRessources+
					"', sizes:='"+record.sizes+"', contentTypes:='"+record.contentTypes+"', times:='"+record.times
					+"', sha512:='"+record.sha512+"', lastUpdate:='"+str(record.lastUpdate)+"', chunks:='"+record.chunks
					+"', revision:='"+str(record.revision)+"' WHERE id="+str(record.id)+"" )
		self.con.commit()
		cur.close()
		

class TextRecord( RessourceRecord ):
	def __init__(self, id=-1, url="", domain="", relatedRessources="", sizes="", contentTypes="", times="", sha512="", lastUpdate="", 
	chunks="", revision=""):
		RessourceRecord.__init__(self, id, url, domain, relatedRessources, sizes, contentTypes, times, sha512, lastUpdate)
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
		self.chunks		= self.unserialiseSimpleList( record.chunks, int )
		self.revision	= int(record.revision)
	
	def getRecord(self):
		return TextRecord(
			id					= self.id,
			url					= self.url,
			domain				= self.domain,
			
			relatedRessources	= self.serializeTupleList( self.relatedRessources),
			sizes				= self.serializeSimpleList( self.sizes),
			contentTypes		= self.serializeSimpleList( self.contentTypes),
			times				= self.serializeSimpleList( self.times),
			sha512					= self.serializeSimpleList( self.sha512),
			
			lastUpdate			= self.lastUpdate,
			
			chunks				= self.serializeSimpleList( self.chunks),
			revision			= self.revision
		)
	


class TextHandler:
	def __init__(self):
		RessourceHandler.__init__(self)
	
	def save(self, text):
		pass
		#SQl
		#if( text.id == -1):
			#text.id = self.manager.insert( text.getRecord() )
		#else:
			#self.manager.save( text.getRecord() )
			
		#Data		
		#cRessource	= libpyRessource.Ressource()
		#cRessource.setId( text.id )
		#cRessource.setCurrentRevision( text.revision )
		#cRessource.setChunkIdsFromList( text.chunks )
		
		#cRessourceHandler = libpyRessource.RessourceHandler()
		#cRessourceHandler.newRevision(cRessource, text.data)
