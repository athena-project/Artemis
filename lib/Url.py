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

class UrlRecord( peewee.Model ):
	
	id 				= peewee.PrimaryKeyField()
	protocol		= peewee.TextField()
	domain 			= peewee.TextField()
	url 			= peewee.TextField()
	lastMd5			= peewee.TextField()
	lastVisited 	= peewee.TimeField()
	relatedRessource= peewee.TextField() #type(link to an sql table):id

class Url:
	def __init__(self,url, o="", t="", charset="", alt=""):
		self.origin 	= o
		self.url		= url
		
		t = t.split(";")
		self.type 		= t[0].strip() # contentType withour charset
		if len(t)>1 & (not charset):
			self.charset	= t[1]
		else:
			self.charset 	= charset
		self.alt 		= alt
		
		
	def size(self):
		return len(self.origin)+len(self.url)+len(self.type)+len(self.charset)+len(self.alt)
		
	def serialize(self):
		return self.origin+"|"+self.url+"|"+self.type+"|"+self.charset+"|"+self.alt


#Static function

def serializeList( l):
	buf = ""
	for url in l:
		buff+=url.serialize()+"~"
	return buf
		
def unserialize( s):
	origin, url, type, charset, alt= "", "", "", "", ""
	i,j,k,n=0,0,0, len(s)
	while j<n:
		if s[j] == "|":
			if k==0:
				origin	= s[i:j]
			if k==1:
				url	= s[i:j]
			if k==2:
				type	=s[i:j]
			if k==3:
				charset=s[i:j]
			if k==4:
				alt	=s[i:j]
				
			i,j,k=j,j+1,k+1
		else:
			j+=1
	return Url( origin, url, type, charset, alt)

def unserializeList( s ):
	l = []
	i,j,n=0,0,len(s)
	while j<n:
		if s[j] == "~":
			l.append( unserialize( s[i:j] ) )
			i,j=j,j+1
		else:
			j+=1
	return l
	
def recordList2list(rL):
	l=[]
	for r in rL:
		l.append( Url( url=r.url ))
	
