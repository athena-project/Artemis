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
from urllib.parse import urlparse
from TcpServer import TcpServer
from TcpClient import TcpClient
from TcpMsg    import TcpMsg
import UrlCacheHandler
import Url
import RobotCacheHandler
from threading import Thread, RLock, Event



class Overseer( Thread ):
	ACTION_CRAWL	= 0
	ACTION_UPDATE	= 1
	
	def __init__(self, action, cPort, slavesAvailable, urlCacheHandler, period, delay, Exit ):
		Thread.__init__(self)
		
		
		self.action				= action 
		self.slavesAvailable	= slavesAvailable
		self.cPort				= cPort
	
		self.urlCacheHandler	= urlCacheHandler
		
		self.period				= period			
		self.delay				= delay
		
		self.manager 			= Url.UrlManager()
		self.redis				= Url.RedisManager()
		
		self.Exit 				= Exit
	
	def crawl(self):
		while not self.Exit.is_set():
			for slaveAdress in self.slavesAvailable:
				t = TcpClient( slaveAdress, self.cPort )
				bundle	= Url.makeCacheBundle(self.urlCacheHandler, MasterThread.secondValidUrl, self.redis,
												self.delay, TcpMsg.T_URL_TRANSFER_SIZE-TcpMsg.T_TYPE_SIZE)
				
				t.send( TcpMsg.T_URL_TRANSFER + bundle)
				self.slavesAvailable.remove( slaveAdress )
			time.sleep( self.period )
	
	def secondValidUrl(url, cacheHandler, redis, delay):
		"""
			Before sending
		"""	
		if( url == None):
			return False
			
		#Check in ram
		if( cacheHandler.exists( url ) ):
			return False
			
		#Sql check			
		try:
			lastVisited = redis.get( url.url )
			if lastVisited != None and (time.time() - lastVisited < delay):
				return False
		except Exception:
			return False
			
		return True
	
	def run(self):
		if self.action == MasterThread.ACTION_CRAWL:
			self.crawl()
		if self.action == MasterThread.ACTION_UPDATE:
			self.update()
		

class Master( TcpServer ):
	"""
	"""
	
	
	def __init__(self, useragent="*", cPort=1646 , port=1645, period=10, domainRules={"*":False},
				protocolRules={"*":False}, originRules={"*":False}, delay = 36000,
				maxRamSize=100) :
		"""
			@domainRules			- domain => true ie allowed False forbiden *=>all
			@param maxMemRobots		- maximun of robot.txt ept in disk cache
			@param urlsPerSlave		- 
		"""
		self.cPort				= cPort #client port
		TcpServer.__init__(self, port)				 #server port
		
		self.useragent 			= useragent
		self.period				= period # delay(second) betwen two crawl
		
		
		self.slavesAvailable	= [] #address1,..
		
		self.domainRules		= domainRules
		self.protocolRules		= protocolRules
		self.originRules		= originRules
		
		self.delay				= delay # de maj
		
		self.maxRamSize			= maxRamSize
		
		self.urlCacheHandler	= UrlCacheHandler.UrlCacheHandler(self.maxRamSize)
		self.robotCacheHandler	= RobotCacheHandler.RobotCacheHandler()		
		
		
		self.initNetworking()
		self.Exit				= Event()
		
	def __del__(self):
		sefl.Exit.set()
		
	def crawl(self):
		master = MasterThread( action = MasterThread.ACTION_CRAWL, cPort = self.cPort,
								slavesAvailable = self.slavesAvailable, urlCacheHandler = self.urlCacheHandler,
								period = self.period,
								delay = self.delay, Exit=self.Exit)
		master.start()
		self.listen()

	def update(self):
		master = MasterThread( action = MasterThread.ACTION_UPDATE, cPort = self.cPort,
								slavesAvailable = self.slavesAvailable, urlCacheHandler = self.urlCacheHandler,
								period = self.period, 
								delay = self.delay, Exit=self.Exit)
		master.start()
		
		self.listen()
		
	### Network ###
	def process(self, type, data, address):
		if type == TcpMsg.T_DONE:
			pass
			
		if type == TcpMsg.T_PENDING:
			self.slavesAvailable.append( address[0] )
			
		if type == TcpMsg.T_URL_TRANSFER:
			self.addUrls( data )
	
	
	### Url Handling ###
	def firstValidUrl(self, url):
		"""
			Before adding to cache
		"""
		#Check in ram
		if( self.urlCacheHandler.exists( url ) ):
			return False
		
		#Chek origin
		if url.origin in self.originRules:
			if not self.originRules[url.origin]:
				return False
		else:
			return False
			
		#Check domain and protocol
		urlP = urlparse( url.url )
		
		if urlP.scheme in self.protocolRules:
		  if not self.protocolRules[urlP.scheme]:
			  False
		elif not self.protocolRules["*"]:
				return False
		
		if urlP.netloc in self.domainRules:
		  if not self.domainRules[urlP.netloc]:
			  False
		elif not self.domainRules["*"]:
				return False
		
		#Robot check
		robot = self.robotCacheHandler.get( urlP.scheme+"://"+urlP.netloc )
		if robot != None and not robot.can_fetch(self.useragent , url.url):
			return False
		
		return True
		
	def addUrls(self, data ):
		urls = Url.unserializeList( data[1:] )
		for url in urls :
			if self.firstValidUrl( url ):
				self.urlCacheHandler.add( url ) 
