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
import time
import urllib.robotparser
from heapq import *

class Item:
	def __init__(self, priority, robot):
		"""	
			@param	priority	-
			@param	robot 		-
			@brief Object use to represent robot in heapq( priority queue)
		"""
		self.priority	= priority
		self.robot 		= robot
	
	def __del__(self):
		if self.robot :
			del self.robot
		
	def __eq__(self,y):
		return self.priority == y.priority
		
	def __ge__(self, y): #x.__ge__(y) <==> x>=y
		return self.priority>=y.priority
		
	def __gt__(self, y): # x.__gt__(y) <==> x>y
		return self.priority>y.priority
	
	def  __le__(self, y): # x.__le__(y) <==> x<=y
		return self.priority<=y.priority
		
	def  __lt__(self, y): # x.__lt__(y) <==> x<y
		return self.priority<y.priority
		
	def incr(self):
		self.priority+=1

class RobotCacheHandler:
	
	def __init__(self, maxRamElmt=10000, lifetime=36000):
		"""
			@param maxRamElmt	- maximun number of robot.txt objects saved in ram
			@param liftime		- lifetime( second ) of a robot object before updating
		"""
		self.maxRamElmt 	= maxRamElmt
		
		self.lifetime 		= lifetime
		self.data = {} #url => parser feed
		
		self.accessMap		= [] # heapq
		
	def add(self, key):
		if len(self.data) > self.maxRamElmt :
			tmp = heappop(self.accessMap)
			del tmp
		try:
			self.data[ key ] = Item( 0, urllib.robotparser.RobotFileParser())
			self.data[ key ].robot.set_url( key )
			self.data[ key ].robot.read()
			self.data[ key ].robot.modified()
			heappush( self.accessMap, self.data[ key ] )
		except Exception:
			return False			
		return True

	def get( self, key ):
		if key in self.data:
			self.data[key].incr()
			if time.time() - self.data[ key ].robot.mtime() < self.lifetime:
				return self.data[key].robot
			else:
				self.data[ key ].robot.read()
				self.data[ key ].robot.modified()
				return self.data[key].robot
		
		if self.add( key ):
			return self.data[ key ].robot
		else :
			return None
