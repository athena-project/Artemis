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
#	@author Severus21
#
import SQLFactory
from Ressource import *
import SQLFactory

import hashlib
import time

#import libpyRessource


class TextManager( RessourceManager):
	def __init__(self, con=None):
		"""
			@brief see Ressource.RessourceManager
		"""
		RessourceManager.__init__(self, con)
		self.table		= "text"
	
	
	def get(self, number, offset=0):
		cur = self.con.cursor()
		cur.execute("SELECT * FROM "+self.table+" ORDER BY id LIMIT "+number+" OFFSET "+offset)
		
		records=[]
		for row in cur: 
			r=TextRecord( row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11] )
			records.append( r )
		cur.close()
		
		return records
	
	
	def getByUrl(self, url):
		cur = self.con.cursor()
		cur.execute("SELECT * FROM "+self.table+" WHERE url='"+url+"'")

		r=None
		for row in cur: #url is a unique id
			r=TextRecord( row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11] )
		cur.close()
		
		return r
	
	def getByUrls(self, urls):
		records	= {}
		buff	= ""
		for url in urls:
			if buff != "":
				buff+= ","
			buff += " '"+url+"' "
		
		cur = self.con.cursor()
		cur.execute("SELECT * FROM "+self.table+" WHERE url IN("+buff+")")

		r=None
		for row in cur: #url is a unique id
			r=TextRecord( row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11] )
			records[ row[1] ]	=	r
		cur.close()
		
		return records
	
	def insert(self, record):
		cur = self.con.cursor()
		cur.execute("INSERT INTO "+self.table+" (url, domain, relatedRessources, sizes, contentTypes, times, sha512, lastUpdate, chunks, revision, parent)"
					+"VALUES ('"+record.url+"', '"+record.domain+"', '"+record.relatedRessources+"', '"+record.sizes
					+"', '"+record.contentTypes+"', '"+record.times+"', '"+record.sha512+"', '"+str(record.lastUpdate)
					+"', '"+record.chunks+"', '"+str(record.revision)+"', '"+str(record.parent)+"')" )
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
			buff += "', '"+record.chunks+"', '"+str(record.revision)+"', '"+str(record.parent)+"')"
		
		cur = self.con.cursor()
		cur.execute("INSERT INTO "+self.table+" (url, domain, relatedRessources, sizes, contentTypes, times, sha512, lastUpdate, chunks, revision, parent)"
					+"VALUES "+buff )
		self.con.commit()
		
		cur.close()
		
		firstId = self.con.insert_id()
		return range( firstId, firstId+len( records ) )
	
	def updateList(self, records):
		buff = ""
		for record in records:
			if buff != "":
				buff+=", "

			buff += "('"+str(record.id)+"', '"+record.url+"', '"+record.domain+"', '"+record.relatedRessources+"', '"+record.sizes
			buff += "', '"+record.contentTypes+"', '"+record.times+"', '"+record.sha512+"', '"+str(record.lastUpdate)
			buff += "', '"+record.chunks+"', '"+str(record.revision)+"', '"+str(record.parent)+"')"
		
		cur = self.con.cursor()
		
		cur.execute("INSERT INTO "+self.table+" (id, url, domain, relatedRessources, sizes, contentTypes, times, sha512, lastUpdate, chunks, revision, parent)"+
					"VALUES "+buff+ " ON DUPLICATE KEY UPDATE url=VALUES(url), domain=VALUES(domain), relatedRessources=VALUES(relatedRessources),"+
					" sizes=VALUES(sizes), contentTypes=VALUES(contentTypes), times=VALUES(times), sha512=VALUES(sha512),"+
					" lastUpdate=VALUES(lastUpdate), chunks=VALUES(chunks), revision=VALUES(revision), parent=VALUES(parent)")
		
		self.con.commit()
		cur.close()
		
	def update(self, record):
		cur = self.con.cursor()
		cur.execute("UPDATE "+self.table+" SET url:='"+record.url+"', domain:='"+record.domain+"', relatedRessources:='"+record.relatedRessources+
					"', sizes:='"+record.sizes+"', contentTypes:='"+record.contentTypes+"', times:='"+record.times
					+"', sha512:='"+record.sha512+"', lastUpdate:='"+str(record.lastUpdate)+"', chunks:='"+record.chunks
					+"', revision:='"+str(record.revision)+"', parent:='"+str(record.parent)+"' WHERE id="+str(record.id)+"" )
		self.con.commit()
		cur.close()
		

class TextRecord( RessourceRecord ):
	def __init__(self, id=-1, url="", domain="", relatedRessources="", sizes="", contentTypes="", times="", sha512="", lastUpdate="", 
	chunks="", revision="", parent=""):
		"""
			@brief see Ressource.RessourceRecord
		"""
		RessourceRecord.__init__(self, id, url, domain, relatedRessources, sizes, contentTypes, times, sha512, lastUpdate, parent)
		self.chunks		= chunks
		self.revision 	= int(revision)


class Text( Ressource ):
	def __init__(self):
		"""
			@brief see Ressource.Ressource
		"""
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
			sha512				= self.serializeSimpleList( self.sha512),
			
			lastUpdate			= self.lastUpdate,
			parent				= self.parent,
			
			chunks				= self.serializeSimpleList( self.chunks),
			revision			= self.revision
		)
	


class TextHandler:
	def __init__(self):
		RessourceHandler.__init__(self)
		#self.p_cManager	= libpyRessource.ChunkManager.create()
		#self.cHandler	= libpyRessource.RessourceHandler( self.p_cManager )
	
	def save(self, text):
		pass
		#f = open("reb/index", "a")
		#f.write(str(text.id)+" "+text.url+"\n")
		#f.close()

		#f2 = open("reb/pages/"+str(text.id), "w") 
		#f2.write(text.data)
		#f2.close()
		#cRessource	= libpyRessource.Ressource()
		#cRessource.setId( text.id )
		#cRessource.setCurrentRevision( text.revision )
		#cRessource.setChunkIdsFromList( text.chunks )

		#self.cHandler.newRevision(cRessource, text.data)
		#text.chunks = cRessource.getChunkIdsList()

		#RessourceHandler.save(self,text)
