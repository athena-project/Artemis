import urllib.request as request
from urllib.parse import urlparse, urljoin
from http.client import HTTPConnection, HTTPSConnection

import copy

from email.utils import formatdate

import time
import hashlib

from collections import deque
from threading import Thread, RLock, Event
from multiprocessing import Process, Queue

import Url
from  AMQPConsumer import *
from  AMQPProducer import *


import logging

from Netarea import Phi #fonction utilisé pour associé une url à une netarea  url -> netarea key

RESSOURCE_BUNDLE_LEN = 10

class In_Interface(AMQPConsumer, Thread ):
	def __init__(self, urls, maxUrls, Exit) :
		"""
			@param urls			incomming RecordUrl type
			@param maxUrls		describe the number of urls in the  buffer
		"""		
		Thread.__init__(self)
		AMQPConsumer.__init__(self, "artemis_master_out")
		
		self.maxUrls		= maxUrls
		self.urls			= urls
		self.Exit			= Exit
		
	def run(self): 
		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while not self.Exit.is_set():
			while len(self.urls)<selfmaxUrls :
				self.channel.wait()
			sleep(1)
		
	def proccess(self, msg):
		self.urls.extend( Url.unserialize( msg.body ) )
		AMQPConsumer.process( self, msg)

class Sender( Thread ): 
	def __init__(self, newUrls, doneUrls, netTree, domainRules, protocolRules, originRules, delay, Exit):
		"""
			@param newUrls			- deque which contains the urls collected by the crawlers
			@param netTree			- AVL which contains netaarea active on the network
			@param domainRules		- { "domain1" : bool (true ie allowed False forbiden) }, "*" is the default rule
			@param protocolRules	- { "protocol1" : bool (true ie allowed False forbiden) }, "*" is the default protocol
			@param originRules		- { "origin1" : bool (true ie allowed False forbiden) }, "*" is the default origin,
				the origin is the parent balise of the url
			@param delay			- default period between two crawl of the same page
			@param Exit 			- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief Send the collected urls to the master
		"""
		Thread.__init__(self)
		self.new_producer			= AMQPProducer.AMQPProducer("artemis_master_in")
		self.new_producer.channel.exchange_declare(exchange='artemis_master_in_direct', type='direct')
		self.new_producer.channel.queue_declare("artemis_master_in", durable=False)

		self.done_producer			= AMQPProducer.AMQPProducer("artemis_master_done")
		self.done_producer.channel.exchange_declare(exchange='artemis_master_done_direct', type='direct')
		self.done_producer.channel.queue_declare("artemis_master_done", durable=False)

		self.newUrls		= newUrls
		self.doneUrls	= doneUrls
		self.netTree		= netTree
		
		self.domainRules	= domainRules 
		self.protocolRules	= protocolRules
		self.originRules	= originRules
		
		self.delay			= delay
		self.alreadySent	= LimitedDict( 1<<22 ) #voir la taille
		self.Exit			= Exit

	def __del__(self):
		logging.info("Sender stopped")

	def is_valid(self, urlRecord):
		"""
			@brief			- it will chek 
				if the url match the domainRules, the protocolRules, the originRules,
				if the url is already in cache 
				if the url has been already visited during the "past delay"
				
		"""
		url = urlRecord.url
		if( url in self.alreadySent and  self.alreadySent[url].is_expediable(self.delay) ):
			return False
		
		if  (url.origin not in self.originRules and not self.originRules["*"])  or  (url.origin in self.originRules and not self.originRules[url.origin]):
				return False

		urlP = urlparse( url )
		if (urlP.scheme not in self.protocolRules and not self.protocolRules["*"]) or  (urlP.scheme in self.protocolRules and not self.protocolRules[urlP.scheme]):
			  return False
		
		if (urlP.netloc not in self.domainRules and not self.domainRules["*"])  or  (urlP.netloc in self.domainRules and not self.domainRules[urlP.netloc]):
			  return False
			  
		self.alreadySend[url]=urlRecord
		return True

	def process(self):
		nUrls=[] #only valid and fresh urls
		
		while self.newUrls:
			urlRecord = self.newUrls.popleft()
			if self.is_valid( urlRecord ):
				nUrls.append( urlRecord )
		
		while nUrls:
			urlRecord 	= nUrls.pop()
			key	= self.netTree.search( Phi(urlRecord) ).netarea
			
			self.new_producer.add_task( serialize(urlRecord), echange="artemis_master_in_direct", routing_key=key  )
			
		while self.doneUrls :
			urlRecord = self.doneUrls.popleft()
			key	= self.netTree.search( Phi(urlRecord) ).netarea
			self.new_producer.add_task( serialize(urlRecord), echange="artemis_master_done_direct", routing_key=key  )

	def run(self):
		while not self.Exit.is_set():
			self.process()
			time.sleep(1)
		
		self.process()

class CrawlerOverseer( Thread ):
	def __init__(self, useragent, maxCrawlers,  urls, doneUrls, newUrls, contentTypes, delay, unorderedRessource, Exit):
		"""
			@param useragent			- 
			@param maxCrawlers			- maximun number of crawlers
			@param urls					- deque which contains the urls received from the master
			@param contentTypes			- dict of allowed content type (in fact allowed rType cf.contentTypeRules.py)
			@param delay				- period between two crawl of the same page
			@param unorderedRessource	- ressources collected waiting for saving in sql( dict : [rType : deque of ressources,..]
			@param newUrls				- deque which contains the urls collected by the crawlers
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief Creates and monitors the crawlers
		"""
		Thread.__init__(self)
		self.useragent			= useragent
			
		self.maxCrawlers 		= maxCrawlers
		
		self.crawlers 			= []
		
		self.urls				= urls
		self.newUrls			= newUrls
		self.doneUrls			= doneUrls
		self.contentTypes		= contentTypes
		self.delay				= delay

		self.unorderedRessource	= unorderedRessource
		self.Exit				= Exit

		is_alive()
		

	def __del__(self):
		self.Exit.set()
		logging.info("CrawlerOverseer stopped")
	
	
	
	def process():
		for i in range(self.maxCrawlers):
			w = Crawler( self.useragent, self.urls, self.doneUrls, self.newUrls, copy.deepcopy(self.contentTypes), self.delay,
						self.unorderedRessource, self.Exit )
			self.crawlers.append( w )
			w.start()
		
	def run(self):
		self.process()
		while not self.Exit.is_set(): # pas encore de role definit en attente despécification utltérieures
			time.sleep( 2 ) 
		
		while len(self.crawlers)>0:
			for i in len(self.crawlers):
				if not self.crawlers[i].is_alive():
					del self.crawlers[i]

class Crawler( Thread ): 
	def __init__(self, useragent,  urls, doneUrls, newUrls, contentTypes, delay, unorderedRessource, Exit):
		"""
			@param urls					- deque which contains the urls received from the master
			@param newUrls				- deque which contains the urls collected by the crawlers
			@param contentTypes			- dict of allowed content type (in fact allowed rType cf.contentTypeRules.py)
			@param delay				- period between two crawl of the same page
			@param unorderedRessource	- ressources collected waiting for saving in sql( dict : [rType : deque of ressources,..]
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief Will get ressources from the web, and will add data to waitingRessources and collected urls to newUrls
		"""
		Thread.__init__(self)
		self.useragent			= useragent
		
		self.urls				= urls
		self.newUrls			= newUrls
		self.doneUrls		= doneUrls
		self.contentTypes		= contentTypes 
		self.delay				= delay
		self.redis 				= redis
				
		self.unorderedRessource	= unorderedRessource
		self.Exit 				= Exit
		
		self.redisUrlManager	= RedisUrlsManager()
		
		self.contentTypesHeader = "*/*;"
		if "*" in contentTypes and  (not self.contentTypes["*"]) :
			self.contentTypesHeader =""
			for key,flag in self.contentTypes:
				if key != "*" and flag:
					self.contentTypesHeader+=key+"; ,"
			
	def process(self):
		try:
			while True:
				urlRecord = self.urls.popleft()
				self.dispatch( urlRecord )
		except Exception as e:
			logging.debug( e )
	
	def run(self):
		while not self.Exit.is_set():
			self.process()
			time.sleep(1)
		self.process()	
			
	def dispatch(self, urlRecord):
		"""
			@param url	-
			@brief selects the right function to  handle the protocl corresponding to the current url( http, ftp etc..)
		"""
		urlObject = urlparse( urlRecord.url )	
		if( urlObject.scheme == "http" or urlObject.scheme == "https"):
			self.http( urlRecord, urlObject )
	
	def http( self, urlRecord, urlObj ): 
		"""
			@param url		-	
			@param urlObj	- ParseResult (see urllib.parse), which represents the current url
			@brief connects to  the remote ressource and get it
		"""
		urlRecord.lastvisited 	= time.time()
		urlRecord.lastcontrolled= urlRecord.lastvisited
		Connector	= HTTPConnection if urlObject.scheme == "http" else HTTPSConnection
		
		if urlRecord.lastvisited != -1:
			conn1 = Connector( urljoin( urlObj.scheme, urlObj.netloc) )
			headers1 = {"If-Modified-Since":formatdate( timeval     = urlRecord.lastvisited, localtime = False, usegmt = True),
						"User-Agent":self.useragent,
						"Accept":self.contentTypesHeader}

			conn1.request("HEAD", urlObj.path, "", headers)
			r1 = conn1.getresponse()
			conn1.close()
			if (r1.status == 301 or r1.status ==302 or r2.status ==307 or r2.status ==308) and "Location" in r1.headers.dict: #redirection
				urlRecord.incr()
				self.newUrls.append( UrlRecord(r1.headers.dict["Location"]) )
				self.doneUrls.append( urlRecord )
				return
			elif r1.status == 304 : #Content unchange
				urlRecord.incr()
				self.doneUrls.append( urlRecord )
				return 
			elif r1.status > 400 : #ie 4xx or 5xx error
				urlRecord.incr()
				self.doneUrls.append( urlRecord )
				logging.debug( r1.status, urlRecord.url, r1.read() )
				return 
			
			
		
		conn2 = Connector( urljoin( urlObj.scheme, urlObj.netloc) )
		headers2 = {"User-Agent":self.useragent,
					"Accept":self.contentTypesHeader}
		
		if urlObj.params == "":
			conn2.request("GET", urlObj.path, urlObj.params, headers)
		else:
			conn2.request("POST", urlObj.path, urlObj.params, headers)
			
		r2 = conn.getresponse()
		if (r2.status == 301 or r2.status ==302 or r2.status ==307 or r2.status ==308) and "Location" in r1.headers.dict: #redirection
			urlRecord.incr()
			self.newUrls.append( UrlRecord(r1.headers.dict["Location"]) )
			self.doneUrls.append( urlRecord )
			return
		elif r1.status != 200 : #ie 4xx or 5xx error
			urlRecord.incr()
			self.doneUrls.append( urlRecord )
			logging.debug( r1.status, urlRecord.url, r1.read() )
			return 
			
			
		#ContentType 
		cT = r.getheader("Content-Type")	
		contentType	= (cT.split(";"))[0].strip()
		
		if (contentType in self.contentTypes and not self.contentTypes[contentType]) or ( not self.contentTypes["*"] or contentType not in contentTypeRules) :
			conn2.close()
			urlRecord.incr()
			self.doneUrls.append( urlRecord )
			return 

		data = r2.read()
		conn2.close()
		
		#Hash
		m_sha512 = hashlib.sha512()
		m_sha512.update(data)
		h_sha512 = m_sha512.hexdigest()
		
		
		
		
		ressource 	= Ressource(0, getClassType( contentType )) 
		metadata	= ressource.getMetadata()
		
		if h_sha512 == urlRecord.lasthash :
			urlRecord.incr()
			self.doneUrls.append( urlRecord )
			return 
		
		urlRecord.lasthash = h_sha512

		
				
		metadata["source_type"]		= self.useragent
		metadata["source_location"]	= url.url
		metadata["source_time"]		= urlRecord.lastvisited
		
		metadata["contentType"]		= contentType
		metadata["sha512"]			= h_sha512
		metadata["size"]			= len( data )
		
		ressource.setData( data)
				
		self.unorderedRessources[ ressource.getClass_type() ].append( (urlRecord, ressource) )
		urls = ressource.extractUrls( urlObj )
		self.newUrls.extend( urls )
		
		urlRecord.decr()
		self.doneUrls.append( urlRecord )

class SQLHandler( Thread ):
	def __init__(self,  number, unorderedRessources, orderedRessources, Exit):	
		"""
			@param number				- insert and update pool size
			@param unorderedRessources	- ressources collected waiting for saving in sql( dict : [rType : deque of ressources,..]
			@param orderedRessources	- after saved in db
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief handle sql requests, inserts newly collected ressources, and updates analysed ones
		"""
		
		Thread.__init__(self); 
		self.managers 			= {}
		self.number				= number
		self.unorderedRessources= unorderedRessources
		self.orderedRessources	= orderedRessources
		
		self.Exit				= Exit

		self.manager			= SQLRessourceManager( SQLFactory.getConn() )
		self.sqlUrlManager		= SQLUrlManager( SQLFactory.getConn() )
		self.redisUrlManager	= redisUrlManager( RedisFactory.getConn() )
					
	def __del__(self):
		logging.info("SQLHandler stopped")
		
	def process(self, class_type):
		for class_type in self.unorderedRessources:
			while len( self.unorderedRessources[class_type])>self.number :
				ressources 	= []
				urls 		= []
				
				for k in range(self.number):
					urlRecord, ressource = self.unorderedRessources[class_type].popleft()
					ressources.append( ressource )
					urls.append( urlRecord, ressource )
					
					#Deduplication
					formerRessource = self.redisUrlManager.get( "ressource_"+urlRecord.lastHash)
					if formerRessource != None :
						metadata.addReference( formerRessource )
				
				self.manager.insert(class_type, ressources)
				self.sqlUrlManager.save(urls)
				self.redisUrlManager.add( ressources, urls)
				
				self.orderedRessources.extend( ressources )
		
	def run(self):
		while not self.Exit.is_set():
			try:
				self.process()
			except Exception as e:
				logging.debug( e )	
					
			time.sleep( 1 )
		
		self.process()
		self.number=1
		self.process()

class WorkerOverseer(Thread):
	def __init__(self, maxWorkers, dfs_path, orderedRessources, savedRessources,  Exit):
		"""
			@param maxWorkers			- maximun number of workers handled by this overseer
			@param orderedRessources	- ressources saved in db (see SQLHandler.preprocessing )
			@param savedRessources		- ressources saved in DFS
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
		"""
		Thread.__init__(self)

		self.orderedRessources	= orderedRessources
		self.savedRessources	= savedRessources
		self.maxWorkers			= maxWorkers
		self.dfs_path			= dfs_path
		self.Exit 				= Exit
		
		self.workers			= []

	def __del__(self):
		self.Exit.set()	
		logging.info( "WorkerOverseer end")
		
	def process(self):
		for i in range(self.maxWorkers):
			w = Worker( self.orderedRessources, self.savedRessources, self.Exit )
			self.workers.append( w )
			w.start()
	
	def run(self):
		self.process()
		while not self.Exit.is_set(): # pas encore de role definit en attente despécification utltérieures
			time.sleep( 2 ) 
		
		while len(self.workers)>0:
			for i in len(self.workers):
				if not self.workers[i].is_alive():
					del self.workers[i]

class Worker(Thread):
	"""
		@brief saves a ressource on DFS
	"""
	def __init__(self, dfs_path, orderedRessources, savedRessources,  Exit):
		Thread.__init__(self)
		
		self.dfs_path			= dfs_path
		self.orderedRessources	= orderedRessources
		self.savedRessources	= savedRessources
		self.Exit 				= Exit
		
	def process(self):
		try:
			while True:
				ressource = self.orderedRessources.popleft()
				ressource.save( self.dfs_path )
				self.savedRessources.append( ressource )
		except Exception as e:
			logging.debug( e )
	
	def run(self):
		while not self.Exist.is_set():
			self.process()
			time.sleep(1)
			
		self.process()

class Out_Interface(AMQPProducer, Thread ):
	def __init__(self, savedRessources, Exit) :
		Thread.__init__(self)
		
		AMQPProducer.__init__(self, "artemis_out")
		self.channel.queue_declare(self.key, durable=False)
		
		self.savedRessources	= savedRessources
		self.Exit				= Exit
		
	def add_tasks(self):
		while self.savedRessources:
			ressources = []
			try:
				for k in range( RESSOURCE_BUNDLE_LEN ) : 
					ressources.append( self.savedRessources.popleft() )
			except Exception :
				pass
			
			if ressources:
				self.add_task( Url.serialize(urls) )
				
	def run(self):
		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while not self.Exit.is_set():
			self.add_tasks()
			sleep(1)
		
		#empty savedRessources
		RESSOURCE_BUNDLE_LEN = 1
		self.add_tasks()

class Server(Process):
	def __init__(self, useragent, maxCrawlers, maxWorkers, delay, sqlNumber, dfs_path, contentTypes,
				domainRules, protocolRules, originRules, maxUrlsSize, maxNewUrlsSize, maxDoneUrlsSize,
				maxUnorderedRessourcesSize, maxOrderedRessourcesSize, maxSavedRessourcesSize) :
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
		AMQPConsumer.__init__(self, "")
		self.channel.exchange_declare(exchange='artemis_monitor_slave_out', type='fanout')
		result = self.channel.queue_declare(exclusive=True, durable=False)
		self.channel.queue_bind(queue=result.method.queue, exchange='artemis_monitor_slave_out')
		
		
		self.useragent			= useragent
		
		self.maxCrawlers		= maxCrawlers
		self.maxWorkers 		= maxWorkers
		
		self.delay				= delay
		self.sqlNumber			= sqlNumber
		self.dfs_path			= dfs_path
		
		self.netTree			= NetareaTree()
		self.contentTypes		= contentTypes
		self.domainRules		= domainRules
		self.protocolRules		= protocolRules
		self.originRules		= originRules
		
		self.urls				= LimitedDeque( maxUrlsSize )
		self.maxUrls			= maxUrlsSize % 2048 # assuming that an url len is less than 2048
		self.newUrls			= LimitedDeque( maxNewUrlsSize )
		self.doneUrls			= LimitedDeque( maxDoneUrlsSize )
		self.unorderedRessources= LimitedDeque( maxUnorderedRessourcesSize )
		self.orderedRessources	= LimitedDeque( maxOrderedRessourcesSize )
		self.savedRessources	= LimitedDeque( maxSavedRessourcesSize )
		

		self.In_Interface_Exit 				= Event()
		self.Sender_Exit 					= Event()
		self.CrawlerOverseer_Exit 			= Event()
		self.SQLHandler_Exit 				= Event()
		self.WorkerOverseer_Exit 			= Event()
		self.Out_Interface					= Event()
		
		for key in class_types:
			self.unorderedRessources[key]	= deque()
			self.orderedRessources[key]		= deque()
			self.savedRessources[key]		= deque()
			
	def __del__(self):
		self.terminate()
	
	def start_sender(self):
		self.sender	= Sender( self.newUrls, self.doneUrls, self.netTree, self.domainRules, self.protocolRules, self.originRules, 
							self.delay, self.Sender_Exit)	
		self.sender.start()
				
	def stop_sender(self):
		self.Sender_Exit.set()
		while self.sender.is_alive():
			time.sleep(1)
	def terminate(self):
		self.In_Interface_Exit.set()
		while self.inInterface.is_alive():
			time.sleep(1)
		
		self.CrawlerOverseer_Exit.set()
		while self.crawlerOverseer.is_alive():
			time.sleep(1)
		
		self.stop_sender()
			
		self.SQLHandler_Exit.set()
		while self.sqlHandler.is_alive():
			time.sleep(1)	
			
		self.WorkerOverseer_Exit.set()
		while self.workerOverseer.is_alive():
			time.sleep(1)
		
		self.Out_Interface_Exit.set()
		while self.outInterface.is_alive():
			time.sleep(1)
			
		Process.terminate(self)
	
	def harness(self):
		self.inInterface	= In_Interface( self.urls, self.maxUrls, self.In_Interface_Exit)
		self.crawlerOverseer= CrawlerOverseer( self.useragent, self.maxCrawlers,  self.urls, self.doneUrls, self.newUrls,
												self.contentTypes, self.delay, self.unorderedRessource, self.CrawlerOverseer_Exit)
		self.start_sender()		
		self.sqlHandler		= SqlHandler(self.numberSql, self.unorderedRessources, self.orderedRessources, self.SQLHandler_Exit)						
		self.workerOverseer	= WorkerOverseer( self.maxWorkers, self.dfs_path, self.orderedRessources, self.savedRessources,  self.WorkerOverseer_Exit)				
		self.outInterface	= Out_Interface( self.savedRessources, self.Out_Interface_Exit) 
		
		self.inInterface.start()
		self.crawlerOverseer.start()
		self.sender.start()
		self.sqlHandler.start()
		self.workerOverseer.start()
		self.outInterface.start()
		
		self.consume()
	
	def run(self):
		self.harness()
		
		while True: 
			self.channel.wait() 
	
	def proccess(self, msg):
		(header, args) =  unserialize( msg.body )
		AMQPConsumer.process( self, msg)
		
		if header == Monitor.HEADER_SENDER_STOP:
			self.stop_sender()
		elif header == Monitor.HEADER_SENDER_START:
			self.netTree	= args
			self.start_sender()

class Slave:
	def __init__(self, serverNumber=1, useragent="*", period=10, maxCrawlers=1, maxWorkers=2,
		delay=86400, sqlNumber=100, dfs_path="", contentTypes={"*":False}, domainRules={"*":False},
		originRules={"*":False}, maxNewUrlsSize=1<<24, maxDoneUrlsSize=1<<24, maxUnorderedRessourcesSize=1<<26,
		maxOrderedRessourcesSize=1<<26, maxSavedRessourcesSize=1<<26) :
		
		self.pool			= []
		self.serverNumber 	= serverNumber
		
		for i in range(self.serverNumber):
			s = Server(useragent, maxCrawlers, maxWorkers, delay, sqlNumber, dfs_path, contentTypes,
				domainRules, protocolRules, originRules, maxUrlsSize, maxNewUrlsSize, maxDoneUrlsSize, maxUnorderedRessourcesSize,
				maxOrderedRessourcesSize, maxSavedRessourcesSize)
			self.pool.append( s )

	def __del__(self):
		for server in self.pool:
			server.terminate() if server.is_alive() else () 
		logging.info("Servers stoped")

	
	def harness(self):
		for server in self.pool:
			server.start()

		logging.info("Servers started")
		self.pool[0].join()
