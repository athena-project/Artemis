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
from TcpServer import TcpServer
from TcpClient import TcpClient
from TcpMsg import TcpMsg 
	
from contentTypeRules import *
import logging

class Sender( Thread ):
	def __init__(self, masterAddress, cPort, newUrls, Exit):
		"""
			@param masterAddress	- ip adress of the master server
			@param cPort 			- port used by the TcpClient to send a block of newly collected urls
			@param newUrls			- deque which contains the urls collected by the crawlers
			@param Exit 			- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief Send the collected urls to the master
		"""
		Thread.__init__(self)
		self.masterAddress	= masterAddress
		self.cPort			= cPort
		self.newUrls		= newUrls
		self.Exit			= Exit
	
	def __del__(self):
		logging.info("Sender stopped")
	
	def run(self):
		while not self.Exit.is_set():
			t = TcpClient( self.masterAddress, self.cPort )

			while self.newUrls :
				bundle	= Url.makeBundle( self.newUrls, TcpMsg.T_URL_TRANSFER_SIZE-TcpMsg.T_TYPE_SIZE ) 
				t.send( TcpMsg.T_URL_TRANSFER + bundle)
			
			
			time.sleep(1)

				
class CrawlerOverseer( Thread ):
	def __init__(self, masterAddress, useragent, cPort, maxCrawlers, period, urls, contentTypes, delay, 
		waitingRessources, newUrls, Exit):
		"""
			@param masterAddress		- ip adress of the master server
			@param useragent			- 
			@param cPort 				- port used by the TcpClient to send a block of newly collected urls
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
		self.masterAddress		= masterAddress
		self.useragent			= useragent
		self.cPort				= cPort
			
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
		minUrls = 2 * self.maxCrawlers
		t = TcpClient( self.masterAddress, self.cPort )
		
		
		while not self.Exit.is_set():
			if len(self.urls) < minUrls:		
				t.send( TcpMsg.T_PENDING )

			while self.urls :
				if len(self.urls) < minUrls:
					t.send( TcpMsg.T_PENDING )

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
		try:
			r = request.urlopen( url.url )	
		except :
			return

		#Statut check
		if( r.status != 200 ):
			return 
			
		#ContentType 
		cT = r.getheader("Content-Type")	
		t = time.time()
		
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

		
		with self.urlsLock:
			self.redis.add( url.url, t)

		rType						= contentTypeRules[ contentType ] 
		ressource					= rTypes[ rType ][0]()
		ressource.url				= url.url
		ressource.data				= data
		
		self.waitingRessources[rType].append( [cT, url.url, urlObj.netloc, data, t, h_sha512] )
		
		#Collected and adding new urls
		urls = ressource.extractUrls( urlObj )
		for url in urls :
			tmpLast = self.redis.get( url.url )
			if time.time() - tmpLast > self.delay:
				self.newUrls.append( url )


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
		insertRessource, updateRessource =[], []

		while i<self.number:
			wrs.append( self.waitingRessources[rType].popleft() )
			urls.append( wrs[-1][1] )
			i+=1
		
		records	= self.managers[rType].getByUrls(urls = urls)
		
		j = 0
		while j<self.number:
			ressource = rTypes[ rType ][0]()
			if urls[j] in records :
				ressource.hydrate( records[ urls[j] ] )
				updateRessource.append( ressource )
			else:
				insertRessource.append( ressource )

			ressource.url					= wrs[j][1]
			ressource.domain				= wrs[j][2]
			ressource.sizes.append(			len(wrs[j][3] ) ) 
			ressource.contentTypes.append( 	wrs[j][0] ) 
			ressource.times.append( 		wrs[j][4] )
			ressource.sha512.append(	 	wrs[j][5]  )
			ressource.lastUpdate			= wrs[j][4]
			ressource.data					= wrs[j][3]
			j+=1
		return (insertRessource, updateRessource)
		
	def run(self):
		while not self.Exit.is_set():
			for rType in self.waitingRessources :
				while( len( self.waitingRessources[rType] ) > self.number ):
					(insertRessources, updateRessources) = self.preprocessing( rType )
					insertRecords, updateRecords	= [], []
					
					for r in insertRessources:
						insertRecords.append( r.getRecord() )
					for r in updateRessources:
						updateRecords.append( r.getRecord() )
					
					if insertRecords :
						ids = self.managers[rType].insertList( insertRecords );
						i	= 0
						while i<len(ids):
							insertRessources[i].id	= ids[i]
							i+=1
					
					if updateRecords:
						self.managers[rType].updateList( updateRecords );
					
					
					for ressource in insertRessources:
						if not ressource.saved:
							self.ressources[rType].append( ressource );
					
					for ressource in updateRessources:
						if not ressource.saved:
							self.ressources[rType].append( ressource );
			
			for rType in self.postRessources :		
				while( len( self.postRessources[rType] ) > self.number ):
					i,records = 0,[]
					while i<self.number :
						records.append( (self.postRessources[rType].popleft()).getRecord() )
						i+=1
							
					self.managers[rType].updateList( records );
					
					
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
			except Exception:
				rType, ressource = "", None
		
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
		i=0 
		while i<self.maxWorkers:
			self.task_queue.put( ('STOP',None) )
			
		print( "WorkerOverseer end")
		
	def run(self):
		i=0
		while i<self.maxWorkers:
			Process(target=Worker, args= (self.task_queue,self.done_queue) ).start()
			i+=1
			
		while not self.Exit.is_set():
			while not self.done_queue.empty():
				rType,ressource	= self.done_queue.get()
				self.postRessources[rType].append(ressource)

			for rType in self.ressources:
				while self.ressources[ rType ] :
					self.task_queue.put( (rType, self.ressources[rType].popleft() ) )

			time.sleep( 1 )

class Slave( TcpServer ):
	def __init__(self, masterAddress="", useragent="*", cPort=1645 , port=1646, period=10, maxWorkers=2, contentTypes={"*":False},
		delay=86400, maxCrawlers=1, sqlNumber=100) :
		"""
			@param masterAddress	- ip adress of the master server
			@param useragent		- 
			@param cPort 			- port used by the TcpClient to send a block of newly collected urls
			@param port				- port used by the TcpServer 
			@param period			- period between to wake up
			@param maxWorkers		- maximun number of workers handled by an instance of WorkerOverseer
			@param contentTypes		- dict of allowed content type (in fact allowed rType cf.contentTypeRules.py)
			@param delay			- period between two crawl of the same page
			@param maxCrawlers		- maximun number of crawlers handled by an instance of CrawlerOverseer
			@param sqlNumber		-
			@brief
		"""
		TcpServer.__init__(self, port)	
			
		self.masterAddress	= masterAddress
		self.useragent		= useragent
		self.cPort			= cPort
		self.period			= period
		
		self.maxCrawlers		= maxCrawlers
		self.maxWorkers 		= maxWorkers
		
		self.delay				= delay
		self.sqlNumber			= sqlNumber
		self.contentTypes		= contentTypes
		
		t = TcpClient( masterAddress, self.cPort )
		t.send( TcpMsg.T_PENDING )
		
		self.initNetworking()
		
		self.Exit 				= Event()
		
		
		self.urls				= deque()
		self.newUrls			= deque()
		
		self.waitingRessources	= {}
		self.ressources			= {}
		self.postRessources		= {}
		for k in rTypes:
			self.waitingRessources[k]	= deque()
			self.ressources[k]			= deque()
			self.postRessources[k]		= deque()
	def __del__(self):
		self.Exit.set()
	
	def harness(self):
		
		self.sender	= Sender( masterAddress = self.masterAddress, cPort = self.cPort, newUrls = self.newUrls, Exit =self.Exit)
		
		self.crawlerOverseer = CrawlerOverseer(masterAddress = self.masterAddress, useragent = self.useragent,
										cPort = self.cPort, maxCrawlers  = self.maxCrawlers, period = self.period, 
										urls = self.urls,  contentTypes=self.contentTypes, delay=self.delay,
										waitingRessources = self.waitingRessources, newUrls = self.newUrls, Exit = self.Exit)
		
		self.sqlHandler	= SQLHandler( number = self.sqlNumber, waitingRessources = self.waitingRessources,
										ressources = self.ressources, postRessources=self.postRessources, Exit = self.Exit)
		self.workerOverseer	= WorkerOverseer( postRessources = self.postRessources, ressources = self.ressources,  maxWorkers = self.maxWorkers, Exit = self.Exit )
		
		self.sqlHandler.start()
		self.workerOverseer.start()
		self.sender.start()
		self.crawlerOverseer.start()
		
		self.listen()
	
	def process(self, type, data, address):
		if type == TcpMsg.T_DONE:
			pass
	
		if type == TcpMsg.T_URL_TRANSFER:
			self.addUrls( data )
	
	def addUrls(self, data ):
		self.urls.extend( Url.unserializeList( data ) )	
