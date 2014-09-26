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
from urllib.parse import urlparse
import peewee
import SQLFactory



class UrlManager:
	def __init__(self):
		self.con = SQLFactory.getConn()
	
	def __del__(self):
		self.con.close()
		
	def getByUrl(self, url):
		cur = self.con.cursor()
		cur.execute("SELECT * FROM urlrecord WHERE url='"+url+"'")

		r=None
		for row in cur: #url is a unique id
			r=UrlRecord( row[0], row[1], row[2], row[3], row[4], row[5] )
		cur.close()
		
		return r
		
	def getByMd5(self, md5):
		l=[]
		
		cur = self.con.cursor()
		cur.execute("SELECT * FROM urlrecord WHERE md5='"+md5+"'")
		for row in cur:
			l.append( UrlRecord( row[0], row[1], row[2], row[3], row[4], row[5] ) )
		cur.close()
		
		return l
	
	def insert(self, record):
		cur = self.con.cursor()
		cur.execute("INSERT INTO urlrecord (protocol, domain, url, lastMd5, lastVisited) VALUES ('"+record.protocol+
					"', '"+record.domain+"', '"+record.url+"', '"+record.lastMd5+"', '"+str(record.lastVisited)+"')" )
		self.con.commit()
		cur.close()
		
	def update(self, record):
		cur = self.con.cursor()
		cur.execute("UPDATE urlrecord SET protocol:='"+record.protocol+"', domain:='"+record.domain+"', url:='"+record.url+
					"', lastMd5:='"+record.lastMd5+"', lastVisited:='"+str(record.lastVisited)+"' WHERE id='"+str(record.id)+"'" )
		self.con.commit()
		cur.close()
		
	def save(self, record):
		if record.id>-1:
			self.update( record )
		else:
			self.insert( record )
		
class UrlRecord:
	def __init__(self, id=-1, protocol="", domain="", url="", lastMd5="", lastVisited=0):
		self.id 			= id
		self.protocol		= protocol
		self.domain 		= domain
		self.url 			= url
		self.lastMd5		= lastMd5
		self.lastVisited 	= float( lastVisited )
		#relatedRessource= peewee.TextField() #type(link to an sql table):id

class Url:
	def __init__(self,url, o="", t="", charset="", alt=""):
		self.origin 	= o
		self.url		= url
		
		t = t.split(";")
		self.type 		= t[0].strip() # contentType withour charset
		if len(t)>1 and (not charset):
			charset = t[1].split("=")
			if len(charset)>1:
				charset	= charset[1]
			else:
				charset = charset[0]
				
		self.charset 	= charset.strip()
		self.alt 		= alt
		
		
	def size(self):
		return len(self.origin)+len(self.url)+len(self.type)+len(self.charset)+len(self.alt)
		
	def serialize(self):
		return self.origin+"|"+self.url+"|"+self.type+"|"+self.charset+"|"+self.alt


#Static function

def serializeList( l):
	buff = ""
	for url in l:
		buff+=url.serialize()+"~"
	return buff
		
def unserialize( s):
	origin, url, type, charset, alt= "", "", "", "", ""
	i,j,k,n=0,0,0, len(s)
	while j<n:
		if s[j] == "|":
			if k==0:
				origin	= s[i:j]
			if k==1:
				url		= s[i:j]
			if k==2:
				type	= s[i:j]
			if k==3:
				charset	= s[i:j]
			if k==4:
				alt	=s[i:j]
				
			i,j,k=j+1,j+1,k+1
		else:
			j+=1
	return Url( url, origin, type, charset, alt)

def unserializeList( s ):
	l = []
	i,j,n=0,0,len(s)
	while j<n:
		if s[j] == "~":
			l.append( unserialize( s[i:j] ) )
			i,j=j+1,j+1
		else:
			j+=1
	return l
	
def recordList2list(rL):
	l=[]
	for r in rL:
		l.append( Url( url=r.url ))
	
