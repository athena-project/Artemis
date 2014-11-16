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
		
class Sender( Thread ):
	def __init__(self, masterAddress, cPort, newUrls, Exit):
		Thread.__init__(self)
		self.masterAddress	= masterAddress
		self.cPort			= cPort
		self.newUrls		= newUrls
		self.Exit			= Exit
	
	def __del__(self):
		print( "Sender end")
	
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
		
		self.manager			= Url.UrlManager()
		self.redis				= Url.RedisManager()

		self.waitingRessources	= waitingRessources #waiting for sql saving
		
		self.Exit				= Exit
		

	def __del__(self):
		self.Exit.set()
		print( "CrawlerOverseer end")
	
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
				if n>0 :
					i=0
					while i<n :
						w = Crawler( urlsLock=self.urlsLock, urls=self.urls, newUrls=self.newUrls,
											contentTypes=self.contentTypes, delay=self.delay, manager=self.manager,
											redis=self.redis, waitingRessources=self.waitingRessources, Exit = self.Exit )
						self.crawlers.append( w )
						w.start()
						i+=1

				time.sleep( self.period ) 
				self.pruneCrawlers()
			time.sleep( self.period ) 

class Crawler( Thread ):
	def __init__(self, urlsLock=None, urls=deque(), newUrls=deque(), contentTypes={"*":False}, delay=86400, manager=None, redis=None, waitingRessources={}, Exit=Event()):
		"""
		"""
		Thread.__init__(self)
		self.urlsLock			= urlsLock
		self.urls				= urls
		self.newUrls			= newUrls
		self.contentTypes		= contentTypes 
		self.delay				= delay
		self.manager 			= manager
		self.redis 				= redis
				
		self.waitingRessources	= waitingRessources
		self.Exit 				= Exit

	def run(self):
		while not self.Exit.is_set():
			with self.urlsLock:
				if not self.urls :
					time.sleep( 1 ) 
					return None
				url = self.urls.popleft()
			
			self.dispatch( url )

				
	### Network handling ###
	def dispatch(self, url):
		urlObject = urlparse( url.url )	
		if( urlObject.scheme == "http" or urlObject.scheme == "https"):
			self.http( url, urlObject )
			
	def http( self, url, urlObj ):
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

		#UrlRecord hydrating
		urlRecord=Url.UrlRecord( protocol=urlObj.scheme, domain=urlObj.netloc, url=url.url )
		

		
		with self.urlsLock:
			try:
				if self.redis.get( url.url ) == 0 :
					self.manager.save( urlRecord )
				self.redis.add( url.url, t)
			except Exception as e:
				return
		
		rType						= contentTypeRules[ contentType ] 
		ressource					= rTypes[ rType ][0]()
		ressource.url				= url.url
		ressource.data				= data
		
		self.waitingRessources[rType].append( [cT, url.url, urlObj.netloc, data, t, h_sha512] )
		
		urls = ressource.extractUrls( urlObj )
		for url in urls :
			tmpLast = self.redis.get( url.url )
			if time.time() - tmpLast > self.delay:
				self.newUrls.append( url )


class SQLHandler( Thread ):							
	def __init__(self,  number, waitingRessources, ressources, postRessources, Exit):	#number per insert, update
		Thread.__init__(self); 
		self.managers 			= {}
		self.number				= number;
		self.waitingRessources	= waitingRessources #waiting for sql
		self.ressources			= ressources		#waiting for disk 
		self.postRessources		= postRessources#saved on disk 
		
		self.Exit				= Exit
		
		self.conn				= SQLFactory.getConn()
		for rType in rTypes :
			self.managers[rType] = rTypes[rType][2]( self.conn )
		
	def __del__(self):
		print( "SQLHandler end")
		
	def preprocessing(self, rType):
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

import sys
def Worker(input, output):
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
			except:
				rType, ressource = "", None
		
		time.sleep(1)
	

class WorkerOverseer(Thread):
	def __init__(self, postRessources={}, ressources={}, maxWorkers=1, Exit=Event() ):
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
	"""
		@param contentTypes 	- content types allowed ( {contentType = charset(def="", ie all charset allowed)})
	"""
	Exit	= Event()
	
	def __init__(self, masterAddress="", useragent="*", cPort=1645 , port=1646, period=10, maxWorkers=2, contentTypes={"*":False},
		delay=86400, maxCrawlers=1, sqlNumber=100) :
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
	
	### Network ###
	def process(self, type, data, address):
		if type == TcpMsg.T_DONE:
			pass
	
		if type == TcpMsg.T_URL_TRANSFER:
			self.addUrls( data )
	
	### CrawlerThread handling ###
	def addUrls(self, data ):
		self.urls.extend( Url.unserializeList( data ) )	
