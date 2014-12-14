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

from TcpMsg    import TcpMsg
import UrlCacheHandler
import Url
import RobotCacheHandler
from threading import Thread, RLock, Event
from collections import deque
import logging
import AMQPConsumer
import AMQPProducer

class Overseer( Thread ):
	ACTION_CRAWL	= 0
	ACTION_UPDATE	= 1
	
	def __init__(self, action, urlCacheHandler, period, delay, lock, Exit ):
		"""
			@param	action			- CRAWL or UPDATE( will crawl again urls already visited )
			@param	cPort			- port used by the TcpClient to send a piece of work
			@param	slavesAvailable - ips of the slaves waiting to working 
			@param	urlCacheHandler - 
			@param	period 			- period between to wake up
			@param	delay 			- period between two crawl of the same page
			@param lock				- RLock object
			@param	Exit 			- stop condition( an event share with Master, when Master die it is set to true )
		"""
		Thread.__init__(self)
		self.producer			= AMQPProducer.AMQPProducer("urls_tasks")
		
		self.action				= action 	
		self.urlCacheHandler	= urlCacheHandler
		
		self.period				= period			
		self.delay				= delay
		
		self.redis				= Url.RedisManager()
		
		self.lock				= lock
		self.Exit 				= Exit
	
	def crawl(self):
		"""
			@brief	The core function, it will dispatch work to the slaves
		"""
		while not self.Exit.is_set():
			with self.lock:
				bundle = Url.makeCacheBundle(self.urlCacheHandler, Overseer.secondValidUrl, self.redis,
												self.delay, TcpMsg.T_URL_TRANSFER_SIZE-TcpMsg.T_TYPE_SIZE)
			if bundle: 
				self.producer.add_task( bundle)
			else:
				time.sleep( self.period )
	
	def secondValidUrl(url, cacheHandler, redis, delay):
		"""
			@param url				-	
			@brief	a second validation, because during url storage, the current url may have been visited by a slave
		"""	
		if( url == None):
			return False

		#Check in ram
		if( cacheHandler.exists( url ) ):
			return False

		#Redis check
		lastVisited = redis.get( url.url ) 
		if time.time() - lastVisited < delay:
			return False


		return True
	
	def run(self):
		if self.action == Overseer.ACTION_CRAWL:
			self.crawl()
		if self.action == Overseer.ACTION_UPDATE:
			self.update()
		

class Master(AMQPConsumer.AMQPConsumer):
	"""
	"""
	
	Exit				= Event()
	def __init__(self, useragent="*", period=10, domainRules={"*":False},
				protocolRules={"*":False}, originRules={"*":False}, delay = 36000,
				maxRamSize=100, numOverseer=1) :
		"""
			@param useragent		- 
			@param period			- period between to wake up
			@param domainRules		- { "domain1" : bool (true ie allowed False forbiden) }, "*" is the default rule
			@param protocolRules	- { "protocol1" : bool (true ie allowed False forbiden) }, "*" is the default protocol
			@param originRules		- { "origin1" : bool (true ie allowed False forbiden) }, "*" is the default origin,
				the origin is the parent balise of the url
			@param delay			- period between two crawl of the same page
			@param maxRamSize		- maxsize of the urls list kept in ram( in Bytes )
			@param numOverseer		- 
		"""
		AMQPConsumer.AMQPConsumer.__init__(self, "new_urls", False)				
		
		self.useragent 			= useragent
		self.period				= period # delay(second) betwen two crawl
		
		#logger.debug("Hello")
		
		self.domainRules		= domainRules
		self.protocolRules		= protocolRules
		self.originRules		= originRules
		
		self.delay				= delay # de maj
		
		self.maxRamSize			= maxRamSize
		
		self.urlCacheHandler	= UrlCacheHandler.UrlCacheHandler(self.maxRamSize)
		self.robotCacheHandler	= RobotCacheHandler.RobotCacheHandler()		
		
		self.numOverseer		= numOverseer
		self.lock				= RLock()
		self.Exit				= Event()
		self.i=0
	def __del__(self):
		self.Exit.set()
		
	def crawl(self):
		for i in range(0, self.numOverseer):
			master = Overseer( action = Overseer.ACTION_CRAWL, urlCacheHandler = self.urlCacheHandler,
								period = self.period,
								delay = self.delay, lock=self.lock, Exit=self.Exit)
			master.start()
		self.consume()
		
	### Network ###
	def proccess(self, msg):
		self.addUrls( msg.body)
	
	
	### Url Handling ###
	def firstValidUrl(self, url):
		self.i+=1
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
		print(self.i)

		return True
		
	def addUrls(self, data ):
		"""
			@bried 			- serialize the data before adding the extracted files in cache
			@param	data	- 
		"""
		#print( data )
		urls = Url.unserializeList( data[1:] )
		for url in urls :
			if self.firstValidUrl( url ):
				self.urlCacheHandler.add( url ) 
