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

import Url

class UrlCacheHandler:
	
	def __init__(self, maxRamSize=10000):
		"""
			@param maxRamSize	- max size of the current cache( bytes )
			@brief provides a kind of dict limited in space, no thread safe
		"""
		self.maxRamSize 	= maxRamSize
		self.currentRamSize	= 0
		self.data = {}
	
	def empty(self):
		return not self.data
		
	def exists(self, elmt):
		return (elmt.url in self.data)
		
	def add(self, elmt):
		size = elmt.size()
		if self.currentRamSize + size < self.maxRamSize :
			self.data[elmt.url] = elmt
			self.currentRamSize += size 		
	
	def get( self ):
		"""
			@return elmt or None if no elmt in cache
		"""
		if not self.data :
			return None
		
		elmt = self.data.popitem()[1]
		self.currentRamSize -= elmt.size()
		return elmt
	
