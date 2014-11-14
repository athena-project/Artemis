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
		"""
			@param	action			- CRAWL or UPDATE( will crawl again urls already visited )
			@param	cPort			- port used by the TcpClient to send a piece of work
			@param	slavesAvailable - ips of the slaves waiting to working 
			@param	urlCacheHandler - 
			@param	period 			- period between to wake up
			@param	delay 			- period between two crawl of the same page
			@param	Exit 			- stop condition( an event share with Master, when Master die it is set to true )
		"""
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
		"""
			@brief	The core function, it will dispatch work to the slaves
		"""
		while not self.Exit.is_set():
			for slaveAdress in self.slavesAvailable:
				
				t = TcpClient( slaveAdress, self.cPort )
				bundle	= Url.makeCacheBundle(self.urlCacheHandler, Overseer.secondValidUrl, self.redis,
												self.delay, TcpMsg.T_URL_TRANSFER_SIZE-TcpMsg.T_TYPE_SIZE)
				
				t.send( TcpMsg.T_URL_TRANSFER + bundle)
				self.slavesAvailable.remove( slaveAdress )
			time.sleep( self.period )
	
	def secondValidUrl(url, cacheHandler, redis, delay):
		"""
			@brief	a second validation, because during url storage, the current url may have been visited by a slave
		"""	
		if( url == None):
			return False

		#Check in ram
		if( cacheHandler.exists( url ) ):
			return False

		#Sql check	
		try:
			lastVisited = redis.get( url.url ) 
			if time.time() - lastVisited < delay:
				return False
		except Exception:
			return False


		return True
	
	def run(self):
		if self.action == Overseer.ACTION_CRAWL:
			self.crawl()
		if self.action == Overseer.ACTION_UPDATE:
			self.update()
		

class Master( TcpServer ):
	"""
	"""
	
	
	def __init__(self, useragent="*", cPort=1646 , port=1645, period=10, domainRules={"*":False},
				protocolRules={"*":False}, originRules={"*":False}, delay = 36000,
				maxRamSize=100) :
		"""
			@param useragent		- 
			@param cPort			- port used by the TcpClient to send a piece of work
			@param port				- port used by the TcpServer 
			@param period			- period between to wake up
			@param domainRules		- { "domain1" : bool (true ie allowed False forbiden) }, "*" is the default rule
			@param protocolRules	- { "protocol1" : bool (true ie allowed False forbiden) }, "*" is the default protocol
			@param originRules		- { "origin1" : bool (true ie allowed False forbiden) }, "*" is the default origin,
				the origin is the parent balise of the url
			@param delay			- period between two crawl of the same page
			@param maxRamSize		- maxsize of the urls list kept in ram( in Bytes )
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
		self.Exit.set()
		
	def crawl(self):
		master = Overseer( action = Overseer.ACTION_CRAWL, cPort = self.cPort,
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
			@brief			- it will chek 
				if the url match the domainRules, the protocolRules, the originRules,
				if the url is already in cache 
				if the url has been already visited during the "past delay"
				
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
		"""
			@bried 			- serialize the data before adding the extracted files in cache
			@param	data	- 
		"""
		urls = Url.unserializeList( data[1:] )
		for url in urls :
			if self.firstValidUrl( url ):
				self.urlCacheHandler.add( url ) 
