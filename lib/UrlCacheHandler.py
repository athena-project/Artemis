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

import Url

class UrlCacheHandler:
	
	def __init__(self, maxRamSize=10000, maxMemSize=1000000, parentDir=""):
		"""
			Warning !!!!! Do not use with thread .....................;
			@param maxRamSize	-
			@param maxMemSize
			@param
		"""
		self.maxRamSize 	= maxRamSize
		self.maxMemSize 	= maxMemSize
		
		self.currentRamSize	= 0
		self.currentMemSize	= 0
		
		self.parentDir 		= parentDir if parentDir[ len(parentDir)-1 ] == "/" else parentDir+"/"

		self.rId			= 0
		self.wId			= 0
		
		self.oStream		= open( self.parentDir+str(self.wId), "w" )
		self.lastStreamSize	= 0 	
		
		self.data = []
	
	def addSorted(self, elmt):
		"ajout dans une liste triée, supposée sans l'éléménet"
		n =  len( self.data )
		i,j, mil=0,n, 0
		while j-i>0: #calcul of the index 
			mil = (i+j)//2
			if self.data[mil].url < elmt.url:
				i = mil+1
			else:
				j = mil -1
			
		self.data.append( self.data[n-1] )
		k=n-1
		while k>mil: #shift right from mil
			self.data[ k ] =  self.data[ k-1 ]
		self.data[ mil ] = elmt 
	
	def exists(self, elmt):
		n =  len( self.data )
		i,j, mil=0,n, 0
		find=False
		while j-i>0 && !find: #calcul of the index 
			mil = (i+j)//2
			if self.data[mil].url == elmt.url :
				find = True
			if self.data[mil].url < elmt.url:
				i = mil+1
			else:
				j = mil -1
		
		return find
		
	def add(self, elmt):
		size = elmt.size()
		if self.currentRamSize + size < self.maxRamSize :
			self.addSorted( elmt )
			currentRamSize += size 
		else :
			if self.currentMemSize + size < self.maxMemSize :
				self.write( elmt, size )
			
	def write(self, elmt, size):
		if self.lastStreamSize + size > self.maxRamSize :
			self.lastStreamSize = 0
			self.oStream.close()
			
			self.wId += 1
			self.oStream = open( self.parentDir+str(self.wId), "w" )
			
		
		oStream.write( elmt.serialize() )
		self.lastStreamSize += size
	
	def get( self ):
		"""
			@return elmt or None if no elmt in cache
		"""
		if self.currentRamSize == 0 :
			if self.currentMemSize == 0 :
				return None
			slef.load()
		
		elmt = self.data.pop()
		self.currentRamSize -= elmt.size()
		return elmt
		
	def load( self ):
		iStream = open( self.parentDir+str( self.rId) )
		buff = ""
		for line in iStream:
			buff += line
		
		self.data=Url.unSerializeList( buff )
		
		self.rId += 1
		self.currentMemSize -= len(buff)
