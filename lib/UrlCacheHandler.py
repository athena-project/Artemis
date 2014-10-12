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
import os

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
		if  parentDir:
			self.parentDir 		= parentDir if  parentDir[ -1 ] == "/"  else parentDir+"/"
		else :
			self.parentDir = ""

		self.rId			= 0
		self.wId			= 0
		
		self.oStream		= open( self.parentDir+str(self.wId), "w" )
		self.lastStreamSize	= 0 	
		
		self.data = {}
	
	def __del__(self):
		self.oStream.close()
		
	def empty(self):
		return (self.currentRamSize>0) or (self.currentMemSize>0)
		
	def exists(self, elmt):
		return (elmt.url in self.data)
		
	def add(self, elmt):
		size = elmt.size()
		if self.currentRamSize + size < self.maxRamSize :
			self.data[elmt.url] = elmt
			self.currentRamSize += size 
		else :
			if self.currentMemSize + size < self.maxMemSize :
				self.write( elmt, size )		
			
	def write(self, elmt, size):
		return
		#if self.lastStreamSize + size > self.maxRamSize :
			#self.lastStreamSize = 0
			#self.oStream.close()
			
			#self.wId += 1
			#self.oStream = open( self.parentDir+str(self.wId), "w" )
			
		
		#self.oStream.write( elmt.serialize() )
		#self.lastStreamSize += size
		#self.currentMemSize		+= size
	
	def get( self ):
		"""
			@return elmt or None if no elmt in cache
		"""
		if self.currentRamSize == 0 :
			return
			#if self.currentMemSize == 0 :
				#return None
			#self.load()
		
		elmt = self.data.popitem()[1]
		self.currentRamSize -= elmt.size()
		return elmt
		
	def load( self ):
		path = self.parentDir+str( self.rId)
		if( os.path.exists(path) ):
			iStream = open( path )
			buff = ""
			for line in iStream:
				buff += line
			
			l=Url.unserializeList( buff )
			for url in l:
				seld.data[url.url]=url
				self.currentRamSize+=url.size()
				
			self.rId += 1
			self.currentMemSize -= len(buff)
			os.remove( path )
		else:
			#error
			pass
