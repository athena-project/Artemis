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
import time
import urllib.robotparser
from collections import deque

class RobotCacheHandler:
	
	def __init__(self, maxRamElmt=10000, lifetime=3600):
		"""
			@param maxRamSize	-
			@param maxMemSize
			@param
		"""
		self.maxRamElmt 	= maxRamElmt
		
		self.currentRamElmt	= 0
		self.lifetime 		= lifetime
		self.data = {} #url => parser feed
		
		self.memId 			= 0 # the hightest id => the latest used robot 
		self.accessMap		= deque() # (url stack )
	
	def add(self, key):
		if self.currentRamElmt  > self.maxRamElmt :
			self.free( )
		
		self.currentRamElmt += 1
		
		
		try:
			self.data[ key ] = urllib.robotparser.RobotFileParser()
			self.data[ key ].set_url( key )
			self.data[ key ].read()
			self.data[ key ].modified()
			self.accessMap.append( key )
		except Exception:
			self.data[ key ] = None
		
	def free(self):
		i,nbr = 0, self.currentRamElmt // 10
		while i<nbr:
			tmp = self.accessMap.popleft()
			del sel.data[tmp]
			
	def get( self, key ):
		if key in self.data:
			if time.time() - self.data[ key ].mtime() < self.lifetime:
				return self.data[key]
			else:
				self.data[ key ].read()
				self.data[ key ].modified()
				return self.data[key]
		
		self.add( key )
		return self.data[ key ]
		
