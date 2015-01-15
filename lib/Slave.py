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

import urllib.request as request
from urllib.parse import urlparse

import time
import hashlib

from collections import deque
from threading import Thread, RLock, Event
from multiprocessing import Process, Queue

import Url
	
from contentTypeRules import *
import AMQPConsumer
import AMQPProducer

import redis_lock

import logging

class Sender( Thread ):
	BUNDLE_SIZE		= 50

	def __init__(self, newUrls, Exit):
		"""
			@param newUrls			- deque which contains the urls collected by the crawlers
			@param Exit 			- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief Send the collected urls to the master
		"""
		Thread.__init__(self)
		self.producer			= AMQPProducer.AMQPProducer("new_urls")
		
		self.newUrls		= newUrls
		self.Exit			= Exit
	
	def __del__(self):
		logging.info("Sender stopped")
	
	def run(self):
		while not self.Exit.is_set():
			while self.newUrls :
				bundle = Url.makeBundle( self.newUrls, self.BUNDLE_SIZE )
				self.producer.add_task( bundle )
			
			time.sleep(1)

				
class CrawlerOverseer( Thread ):
	def __init__(self, useragent, maxCrawlers, period, urls, contentTypes, delay, 
		waitingRessources, newUrls, Exit):
		"""
			@param useragent			- 
			@param maxCrawlers			- maximun number of crawlers
			@param period				- period between to wake up
			@param urls					- deque which contains the urls received from the master
			@param contentTypes			- dict of allowed content type (in fact allowed rType cf.contentTypeRules.py)
			@param delay				- period between two crawl of the same page
			@param waitingRessources	- ressources collected waiting for saving in sql( dict : [rType : deque of ressources,..]
			@param newUrls				- deque which contains the urls collected by the crawlers
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief Creates and monitors the crawlers
		"""
		Thread.__init__(self)
		self.useragent			= useragent
			
		self.period				= period
		self.maxCrawlers 		= maxCrawlers
		
		self.crawlers 			= []
		
		self.newUrls			= newUrls
		self.urls				= urls
		self.contentTypes		= contentTypes
		self.delay				= delay

		self.urlsLock 			= RLock()
		
		self.redis				= Url.RedisManager()

		self.waitingRessources	= waitingRessources
		
		self.Exit				= Exit
		

	def __del__(self):
		self.Exit.set()
		logging.info("CrawlerOverseer stopped")
	
	def pruneCrawlers(self):
		i=0
		while i<len(self.crawlers) :
			if not self.crawlers[i].is_alive():
				del self.crawlers[i]
			i+=1
		
	def run(self):
		while not self.Exit.is_set():
			while self.urls :
				n = self.maxCrawlers-len(self.crawlers)
				for i in range(0,n):

					w = Crawler( urlsLock=self.urlsLock, urls=self.urls, newUrls=self.newUrls,
										contentTypes=self.contentTypes, delay=self.delay, redis=self.redis,
										waitingRessources=self.waitingRessources, Exit = self.Exit )
					self.crawlers.append( w )
					w.start()

				time.sleep( self.period ) 
				self.pruneCrawlers()

			time.sleep( self.period ) 

class Crawler( Thread ):
	def __init__(self, urlsLock=None, urls=deque(), newUrls=deque(), contentTypes={"*":False}, delay=86400, redis=None, 
		waitingRessources={}, Exit=Event()):
		"""
			@param urlsLock	- RLock with to secure access to urls
			@param urls					- deque which contains the urls received from the master
			@param newUrls				- deque which contains the urls collected by the crawlers
			@param contentTypes			- dict of allowed content type (in fact allowed rType cf.contentTypeRules.py)
			@param delay				- period between two crawl of the same page
			@param redis				- a redis handler
			@param waitingRessources	- ressources collected waiting for saving in sql( dict : [rType : deque of ressources,..]
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief Will get ressources from the web, and will add data to waitingRessources and collected urls to newUrls
		"""
		Thread.__init__(self)
		self.urlsLock			= urlsLock
		self.urls				= urls
		self.newUrls			= newUrls
		self.contentTypes		= contentTypes 
		self.delay				= delay
		self.redis 				= redis
				
		self.waitingRessources	= waitingRessources
		self.Exit 				= Exit

	def run(self):
		url="" 
		while not self.Exit.is_set():
			with self.urlsLock:
				if self.urls :
					url = self.urls.popleft()
			if not url:
				time.sleep(1)
			else:
				self.dispatch( url )
				url=""

				
	### Network handling ###
	def dispatch(self, url):
		"""
			@param url	-
			@brief selects the right function to  handle the protocl corresponding to the current url( http, ftp etc..)
		"""
		urlObject = urlparse( url.url )	
		if( urlObject.scheme == "http" or urlObject.scheme == "https"):
			self.http( url, urlObject )
			
	def http( self, url, urlObj ):
		"""
			@param url		-	
			@param urlObj	- ParseResult (see urllib.parse), which represents the current url
			@brief connects to  the remote ressource and get it
		"""
		t = time.time()
		with self.urlsLock:
			if t - self.redis.get( url.url ) < self.delay:
				return False
			
			lock = redis_lock.Lock(self.redis, url.url)
			
			if not lock.acquire(blocking=False) :
				return False
			
			self.redis.add( url.url, t)
			lock.reset()
		
		try:
			r = request.urlopen( url.url )
		except Exception as e:
			logging.debug(e)
			return
		#print( self.ident, "  ",time.time()-t)
		#Statut check
		if( r.status != 200 ):
			return 
			
		#ContentType 
		cT = r.getheader("Content-Type")	
		
		#ContentType parsing
		cTl=cT.split(";")
		contentType	= cTl[0].strip()
		

		##Chek contentType
		if contentType in self.contentTypes:
			if not self.contentTypes[contentType]:
				return 
		elif (not self.contentTypes["*"]) or (contentType not in contentTypeRules):
			return 

		data = r.read()
		
		#Hash
		m_sha512 = hashlib.sha512()
		m_sha512.update(data)
		h_sha512 = m_sha512.hexdigest()
		
		
		if len(cT)>1:
			charset = cTl[1].split("=")
			if len(charset)>1:
				charset	= charset[1].strip()
			else:
				charset = charset[0].strip()
			data = str(data.decode(charset.lower()))

		rType						= contentTypeRules[ contentType ] 
		ressource					= rTypes[ rType ][0]()
		ressource.url				= url.url
		ressource.data				= data
		
		self.waitingRessources[rType].append( [cT, url.url, urlObj.netloc, data, t, h_sha512] )
		
		#Collected and adding new urls
		urls = ressource.extractUrls( urlObj )
		self.newUrls.extend( urls )


class SQLHandler( Thread ):							
	def __init__(self,  number, waitingRessources, ressources, postRessources, Exit):	#number per insert, update
		"""
			@param number				-
			@param waitingRessources	- ressources collected waiting for saving in sql( dict : [rType : deque of ressources,..]
			@param ressources			- preprocessed ressources (see SQLHandler.preprocessing )
			@param postRessources		- ressources already inserted in SQL db, analyzed by worker and waiting for an SQL update
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief handle sql requests, inserts newly collected ressources, and updates analysed ones
		"""
		
		Thread.__init__(self); 
		self.managers 			= {}
		self.number				= number;
		self.waitingRessources	= waitingRessources #waiting for sql
		self.ressources			= ressources		#waiting for disk 
		self.postRessources		= postRessources	#saved on disk 
		
		self.Exit				= Exit
		
		self.conn				= SQLFactory.getConn()
		for rType in rTypes :
			self.managers[rType] = rTypes[rType][2]( self.conn )
					
	def __del__(self):
		logging.info("SQLHandler stopped")
		
	def preprocessing(self, rType):
		"""
			@param rType	- see contentTypeRules.py
			@brief 
		"""
		wrs, urls, i=[], [], 0
		ressources = []

		for i in range(0, self.number):
			wrs.append( self.waitingRessources[rType].popleft() )
			urls.append( wrs[-1][1] )
		
		records	= self.managers[rType].getByUrls(urls = urls)
		
		for j in range(0, self.number):
			ressource = rTypes[ rType ][0]()
			if urls[j] in records :
				ressource.hydrate( records[ urls[j] ] )
			ressources.append( ressource )
			
			ressource.url					= wrs[j][1]
			ressource.domain				= wrs[j][2]
			ressource.sizes.append(			len(wrs[j][3] ) ) 
			ressource.contentTypes.append( 	wrs[j][0] ) 
			ressource.times.append( 		wrs[j][4] )
			ressource.sha512.append(	 	wrs[j][5]  )
			ressource.lastUpdate			= wrs[j][4]
			ressource.data					= wrs[j][3]
			
		return ressources
		
	def process(self):
		for rType in self.waitingRessources :
			while( len( self.waitingRessources[rType] ) > self.number ):
				ressources 	= self.preprocessing( rType )
				records, urls		= [], []
				
				for r in ressources:
					records.append( r.getRecord() )
					urls.append( r.url ) 
				
				self.managers[rType].updateList( records )
				
				savedRecords = self.managers[rType].getByUrls( urls )
				for ressource in ressources :
					ressource.id = savedRecords[ ressource.url ].id
				
				for ressource in ressources:
					if not ressource.saved:
						self.ressources[rType].append( ressource );
				
		
		for rType in self.postRessources :		
			while( len( self.postRessources[rType] ) > self.number ):
				records = []
				for i in range(0, self.number):
					records.append( (self.postRessources[rType].popleft()).getRecord() )
						
				self.managers[rType].updateList( records );
		
		
	def run(self):
		while not self.Exit.is_set():
			try:
				self.process()
			except Exception as e:
				logging.error( e )	
					
			time.sleep( 1 );

def Worker(input, output):
	"""
		@param input	- multiprocessing.Queue, ressources which must be analyzed
		@param input	- multiprocessing.Queue, ressources already analyzed
		@brief	
	"""
	handlers		= {}
	rType,ressource = "", None
	for k in rTypes:
		handlers[k]= rTypes[k][3]()

	while rType != 'STOP':
		while not input.empty():
			try:
				rType,ressource	= input.get()
				if rType != 'STOP':
					handlers[rType].save( ressource ) 
					output.put( (rType,ressource) )
			except Exception as e:
				rType, ressource = "", None
				logging.debug(e)
		time.sleep(1)
	

class WorkerOverseer(Thread):
	def __init__(self, postRessources={}, ressources={}, maxWorkers=1, Exit=Event() ):
		"""
			@param postRessources		- ressources already inserted in SQL db, analyzed by worker and waiting for an SQL update
			@param maxWorkers			- maximun number of workers handled by this overseer
			@param ressources			- preprocessed ressources (see SQLHandler.preprocessing )
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief Creates and feeds worker's instance, and adding worker's output to postRessources
		"""
		Thread.__init__(self);
		self.postRessources	= postRessources
		self.ressources			= ressources
		self.maxWorkers			= maxWorkers
		self.Exit 				= Exit
		
		self.task_queue 		= Queue()
		self.done_queue 		= Queue()

	def __del__(self):
		for i in range(0, self.maxWorkers) :
			self.task_queue.put( ('STOP',None) )
			
		logging.info( "WorkerOverseer end")
		
	def run(self):
		for i in range(0, self.maxWorkers):
			Process(target=Worker, args= (self.task_queue,self.done_queue) ).start()
			
		while not self.Exit.is_set():
			while not self.done_queue.empty():
				rType,ressource	= self.done_queue.get()
				self.postRessources[rType].append(ressource)

			for rType in self.ressources:
				while self.ressources[ rType ] :
					self.task_queue.put( (rType, self.ressources[rType].popleft() ) )

			time.sleep( 1 )

class Server(Process, AMQPConsumer.AMQPConsumer ):
	def __init__(self, useragent="*", period=10, maxWorkers=2, contentTypes={"*":False},
		delay=86400, maxCrawlers=1, sqlNumber=100, maxNewUrls=10000) :
		"""
			@param useragent		- 
			@param period			- period between to wake up
			@param maxWorkers		- maximun number of workers handled by an instance of WorkerOverseer
			@param contentTypes		- dict of allowed content type (in fact allowed rType cf.contentTypeRules.py)
			@param delay			- period between two crawl of the same page
			@param maxCrawlers		- maximun number of crawlers handled by an instance of CrawlerOverseer
			@param sqlNumber		-
			@brief
		"""
		Process.__init__(self)
		AMQPConsumer.AMQPConsumer.__init__(self, "urls_tasks", False)						
		self.useragent		= useragent
		self.period			= period
		
		self.maxCrawlers		= maxCrawlers
		self.maxWorkers 		= maxWorkers
		
		self.delay				= delay
		self.sqlNumber			= sqlNumber
		self.contentTypes		= contentTypes
		
		
		self.Exit 				= Event()
		
		
		self.urls				= deque()
		self.newUrls			= deque( maxlen = maxNewUrls )
		
		self.waitingRessources	= {}
		self.ressources			= {}
		self.postRessources		= {}
		for k in rTypes:
			self.waitingRessources[k]	= deque()
			self.ressources[k]			= deque()
			self.postRessources[k]		= deque()
	def __del__(self):
		self.Exit.set()
	
	def terminate(self):
		self.Exit.set()
		Process.terminate(self)
	
	def harness(self):
		
		self.sender	= Sender( newUrls = self.newUrls, Exit =self.Exit)
		
		self.crawlerOverseer = CrawlerOverseer(useragent = self.useragent,
										maxCrawlers  = self.maxCrawlers, period = self.period, 
										urls = self.urls,  contentTypes=self.contentTypes, delay=self.delay,
										waitingRessources = self.waitingRessources, newUrls = self.newUrls, Exit = self.Exit)
		
		self.sqlHandler	= SQLHandler( number = self.sqlNumber, waitingRessources = self.waitingRessources,
										ressources = self.ressources, postRessources=self.postRessources, Exit = self.Exit)
		self.workerOverseer	= WorkerOverseer( postRessources = self.postRessources, ressources = self.ressources,  maxWorkers = self.maxWorkers, Exit = self.Exit )
		
		self.sqlHandler.start()
		self.workerOverseer.start()
		self.sender.start()
		self.crawlerOverseer.start()
		self.consume()
	
	def run(self):
		self.harness()
	
	def consume(self):
		try:
			self.channel.basic_consume(callback=self.proccess, queue=self.key)
			maxUrls = 100 * self.maxCrawlers
			while True:
				while True and (len(self.urls) < maxUrls) :
					self.channel.wait()
				time.sleep(1)
		except Exception as e:
			logging.error( e )
			time.sleep(1)
			#self.consume()
	def proccess(self, msg):
		self.addUrls( msg.body)
	
	def addUrls(self, data ):
		self.urls.extend( Url.unserializeList( data ) )


class Slave:
	def __init__(self, serverNumber=1, useragent="*", period=10, maxWorkers=2, contentTypes={"*":False},
		delay=86400, maxCrawlers=1, sqlNumber=100, maxNewUrls=10000) :
			
		self.pool			= []
		self.serverNumber 	= serverNumber
		
		for i in range(0, self.serverNumber):
			s = Server(useragent, period, maxWorkers, contentTypes, delay, maxCrawlers, sqlNumber, maxNewUrls)
			self.pool.append( s )
			
		logging.info("Servers started")
	
	def __del__(self):
		for server in self.pool:
			server.terminate() if server.is_alive() else () 
		logging.info("Servers stoped")

	
	def harness(self):
		for server in self.pool:
			server.start()
		self.pool[0].join()
