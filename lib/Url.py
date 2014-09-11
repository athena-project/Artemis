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

class Url:
	def __init__(self, url, t, charset, alt):
		self.url=url
		self.type = t
		self.charset = charset
		self.alt =alt
		
	def serialize(self):
		return self.url+"|"+self.type+"|"+self.charset+"|"+self.alt
		
	def serializeList( l):
		buf = ""
		for url in l:
			buff+=url.serialize()
		return buf
			
	def unserialize( s):
		url,type,charset,alt="","","",""
		i,j,k,n=0,0,0, len(n)
		while i<n:
			if s[j] == "|":
				if k==0:
					url	= s[i:j]
				if k==1:
					type	=s[i:j]
				if k==2:
					charset=s[i:j]
				if k==3:
					alt	=s[i:j]
					
				i,j,k=j,j+1,k+1
			else:
				j+=1
		return Url( url, type, charset, alt)
	
	def unserializeList( s ):
		l = []
		i,j,n=0,0,0, len(n)
		while i<n:
			if s[j] == ":":
				l.append( unserialize( s[i:j] ) )
				i,j=j,j+1
			else:
				j+=1
		return l
