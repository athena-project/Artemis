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

class RessourceManager:
	def __init__(self, con=None):
		"""
			@brief manage the SQL request 
		"""
		self.con = con if con != None else SQLFactory.getConn()
		self.table	= ""
		
	def getByUrl(self, url):
		cur = self.con.cursor()
		cur.execute("SELECT * FROM "+self.table+" WHERE url='"+url+"'")

		r=None
		for row in cur: #url is a unique id
			r=RessourceRecord( row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9] )
		cur.close()
		
		return r
	
	def insert(self, record):
		cur = self.con.cursor()
		cur.execute("INSERT INTO "+self.table+" (url, domain, relatedRessources, sizes, contentTypes, times, sha512, lastUpdate, parent)"
					+"VALUES ('"+record.url+"', '"+record.domain+"', '"+record.relatedRessources+"', '"+record.sizes
					+"', '"+record.contentTypes+"', '"+record.times+"', '"+record.sha512+"', '"+str(record.lastUpdate)
					+"',  '"+str(record.parent)+"')" )
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
			buff += "', '"+record.contentTypes+"', '"+record.times+"', '"+record.sha512+"', '"
			buff += str(record.lastUpdate)+"', '"+str(record.parent)+"')"
		
		cur = self.con.cursor()
		cur.execute("INSERT INTO "+self.table+" (url, domain, relatedRessources, sizes, contentTypes, times, sha512, lastUpdate, parent)"
					+"VALUES "+buff )			
		self.con.commit()

		cur.close()
		
		firstId = self.con.insert_id()
		return range( firstId, firstId+len( records ) )
		
	def update(self, record):
		cur = self.con.cursor()
		cur.execute("UPDATE "+self.table+" SET url:='"+record.url+"', domain:='"+record.domain+"', relatedRessources:='"+record.relatedRessources+
					"', sizes:='"+record.sizes+"', contentTypes:='"+record.contentTypes+"', times:='"+record.times+
					+"', sha512:='"+record.sha512+"', lastUpdate:='"+str(record.lastUpdate)
					+"', parent:='"+str(record.parent)+"' WHERE id='"+str(record.id)+"'" )
		self.con.commit()
		cur.close()
		
	def save(self, record):
		if record.id>-1:
			self.update( record )
		else:
			self.insert( record )
	
class RessourceRecord:
	def __init__(self, id=-1, url="", domain="", relatedRessources="", sizes="", contentTypes="", times="", sha512="", lastUpdate="", parent=""):
		"""
			@brief represents a ressource object, used to sql save
		"""
		self.id 				= int(id)
		self.url 				= url
		self.domain 			= domain
		self.relatedRessources 	= relatedRessources
		self.sizes 				= sizes
		self.contentTypes 		= contentTypes
		self.times 				= times
		self.sha512 				= sha512
		self.lastUpdate 		= float(lastUpdate)
		self.parent				= int( parent ) #urlrecord id parent

class Ressource:
	def __init__(self):
		"""
			@brief	represents a web ressource, abstract class
		"""
		self.id = -1
		self.url = ""
		self.domain = ""
		self.relatedRessources = [] # [(type, id)]
		
		self.sizes = []
		self.contentTypes = []
		self.times = []
		self.sha512 = []
		
		self.lastUpdate = 0
		self.parent		= -1
		
		self.data = ""
		self.saved=False # False never been saved by RessourceHandler, True yes
	
	def hydrate(self, record):
		"""
			@param record	- see RessourceRecord
			@brief builds an object ressource from a recordRessource
		"""
		if record == None:
			return 
			
		self.id 				= record.id
		self.url				= record.url
		self.domain				= record.domain
			
		self.relatedRessources	= self.unserializeTupleList( record.relatedRessources, str, int )
		self.sizes				= self.unserialiseSimpleList( record.sizes, int)
		self.contentTypes		= self.unserialiseSimpleList( record.contentTypes, str)
		self.times				= self.unserialiseSimpleList( record.times, float)
		self.sha512				= self.unserialiseSimpleList( record.sha512, str )
		
		self.lastUpdate			= record.lastUpdate
		self.parent				= record.parent
	
	def extractUrls(self, parentUrl):
		return []
	
	def serializeSimpleList(self, l):
		s = ""
		for x in l:
			s+=str(x)+":"
		return s[0:len(s)]
		
	def unserialiseSimpleList(self, s, f):
		l  = []
		begin=0
		end=0
		i=0
		n=len(s)
		while i<n :
			if( s[i] == ":" ):
				end = i
				l.append( f(s[begin : end]) )
				begin = i+1
			i+=1
			
		return l
		
	def serializeTupleList(self, l):
		s = ""
		for (a,b) in l:
			s+=str(a)+"|"+str(b)+":"
		return s[0:len(s)]
		
	def unserializeTuple(self, s, f1, f2):
		find = False
		i=0
		n=len(s)
		while( i<s and find == False):
			if( s[i] == "|"):
				find=True
			i+=1
		
		a = s[0:i-2]
		b = s[i:]
		return( f1(a),f2(b) )
		
	def unserializeTupleList(self, s, f1, f2):
		def identity (x): return x
		l  = []
		tmpL = self.unserialiseSimpleList(s, identity)
		for x in tmpL:
			l.append( self.unserializeTuple( x , f1, f2) )
		return l
	
	def getRecord(self):
		return RessourceRecord(
			id					= self.id,
			url					= self.url,
			domain				= self.domain,
			
			relatedRessources	= self.serializeTupleList( self.relatedRessources ),
			sizes				= self.serializeSimpleList( self.sizes ),
			contentTypes		= self.serializeSimpleList( self.contentTypes ),
			times				= self.serializeSimpleList( self.times ),
			sha512					= self.serializeSimpleList( self.sha512 ),
			
			lastUpdate			= self.lastUpdate,
			parent				= self.parent
		)
	
class RessourceHandler:
	def __init__(self):
		pass
	
	def save(self, ressource):
		ressource.saved = True		
