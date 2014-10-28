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
import sys
import urllib.request as request
from urllib.parse import urlparse
from threading import Thread, RLock
import Url
from TcpServer import TcpServer
from TcpClient import TcpClient
from TcpMsg import TcpMsg 
import time
import Ressource	
from contentTypeRules import *
import hashlib


class WorkerThread( Thread ):
	def __init__(self, urlsLock=None, urls=[], newUrls=[], contentTypes={"*":False}, delay=86400, manager=None, waitingRessources=[]):
		"""
		"""
		Thread.__init__(self)
		self.urlsLock			= urlsLock
		self.urls				= urls
		self.newUrls			= newUrls
		self.contentTypes		= contentTypes 
		self.delay				= delay
		self.manager 			= manager
				
		self.waitingRessources	= waitingRessources
	
	def run(self):
		while True:
			with self.urlsLock:
				if not self.urls :
					return None
				url = self.urls.pop()
			
			self.dispatch( url )

				
	### Network handling ###
	def dispatch(self, url):
		urlObject = urlparse( url.url )	
		if( urlObject.scheme == "http" or urlObject.scheme == "https"):
			self.http( url, urlObject )
		#if( urlObject.scheme == "ftp" or urlObject.scheme == "ftps"):
		#	self.ftp( url )
		else :
			pass
			#log
			
	def http( self, url, urlObj ):
		#print("under way")
		try:
			r = request.urlopen( url.url )	
		except :
			#log
			#print("failes")	
			return
		#ContentType 
		cT = r.getheader("Content-Type")
		#print("under way2")
		#Statut check
		if( r.status != 200 ):
			return 
			
			
		t = time.time()
		#ContentType parsing
		cTl=cT.split(";")
		contentType	= cTl[0].strip()
		charset		= "UTF-8"
		if len(cT)>1:
			charset = cTl[1].split("=")
			if len(charset)>1:
				charset	= charset[1].strip()
			else:
				charset = charset[0].strip()

		##Chek contentType
		if contentType in self.contentTypes:
			if not self.contentTypes[contentType]:
				return 
		elif not self.contentTypes["*"]:
			return 
		elif contentType not in contentTypeRules:
			#log
			return 
		
		#print("content type ok")
		data = r.read()
		#Hash
		m_sha512 = hashlib.sha512()
		m_sha512.update(data)
		h_sha512 = m_sha512.hexdigest()
		
		data				= str(data.decode(charset.lower()))

		#UrlRecord hydrating
		urlRecord=Url.UrlRecord( protocol=urlObj.scheme, domain=urlObj.netloc, url=url.url )
		urlRecord.lastsha512		= h_sha512
		urlRecord.lastVisited	= t
		
		with self.urlsLock:
			try:
				self.manager.save( urlRecord )
			except Exception as e:
				return
		
		rType						=  contentTypeRules[ contentType ] 
		ressource					= rTypes[ rType ][0]()
		ressource.url				= url.url
		ressource.data				= data
		self.newUrls.extend( ressource.extractUrls( urlObj ) )
		self.waitingRessources.append( [rType, cT, url.url, urlObj.netloc, data, t, h_sha512] )
	#def ftp( self, url):
	#	r = request.urlopen( url)	
	#	if( r.status == 200 ):
	#		
	#	else:
	#		#log
	
	def save(self, url, urlObj, urlRecord, cT, data):
		#print("begin false save")
		
		
		
		rType				=  contentTypeRules[ contentType ] 
		ressourceHandler	= rTypes[ rType ][3]
		ressourceRecord		= self.managers[rType].getByUrl( url=url.url )
		ressource			= rTypes[ rType ][0]()
		ressource.hydrate( ressourceRecord )
		t 					= time.time()

		
		
		#hash traitement
		#à faire
		

		#Ressource hydrating
		ressource.url					= url.url
		ressource.domain				= urlObj.netloc
		ressource.sizes.append(			len(data ) ) 
		ressource.contentTypes.append( 	cT ) 
		ressource.times.append( 		t )
		ressource.sha512.append(	 		h_sha512  )
		ressource.lastUpdate			= t
		#if h_sha512 == ressource.sha512[-1]:
		ressource.data				= data
	
		#ressourceHandler.save( ressource )	
		
		#Feed the slave with the links owned by the current ressource
		self.newUrls.extend( ressource.extractUrls( urlObj ) )
		t = time.time()-t
		#print(t)
		
class UrlSender( Thread ):
	def __init__(self, masterAddress, cPort, newUrls):
		Thread.__init__(self)
		self.masterAddress	= masterAddress
		self.cPort			= cPort
		self.newUrls		= newUrls
	
	def run(self):
		while True:
			t = TcpClient( self.masterAddress, self.cPort )
			while self.newUrls :
				t.send( TcpMsg.T_URL_TRANSFER + 
					Url.makeBundle( self.newUrls, TcpMsg.T_URL_TRANSFER_SIZE-TcpMsg.T_TYPE_SIZE ) )
			time.sleep(1)

class SQLHandler( Thread ):							
	def __init__(self, managers, number, waitingRessources, ressources):	#number per insert, update
		Thread.__init__(self);
		self.managers 			= managers; #{"rtype"=>obj}
		self.number				= number;
		self.waitingRessources	= waitingRessources #waiting for sql
		self.records			= {}				#already preprocess
		self.ressources			= ressources		#waiting for disk 
		
		for rType in rTypes :
			self.records[rType]=[]
		
	def preprocessing(self, n):
		i,n = 0, min(n, len(self.waitingRessources))
		while i<n:
			wR	= self.waitingRessources.pop()
			rType, cT, url, domain, data, t, h_sha512 = wR[0], wR[1], wR[2], wR[3], wR[4], wR[5], wR[6]
			
			ressourceRecord		= self.managers[rType].getByUrl( url=url )
			ressource			= rTypes[ rType ][0]()
			ressource.hydrate( ressourceRecord )

			ressource.url					= url
			ressource.domain				= domain
			ressource.sizes.append(			len(data ) ) 
			ressource.contentTypes.append( 	cT ) 
			ressource.times.append( 		time.time() )
			ressource.sha512.append(	 	h_sha512  )
			ressource.lastUpdate			= t
			#if h_sha512 == ressource.sha512[-1]:
			ressource.data				= data
			self.records[rType].append( ressource )
			i+=1
	
	def run(self):
		while True:
			self.preprocessing( self.number )
			for rType in self.records :
				records = self.records[rType]
				while( len( records ) > self.number ):
					i, l1, l2, l3, il2 = 0, [], [], [], [] #l2 insertion, l3 update, il2 correspondace ressource id
					while i < self.number:
						l1.append( records.pop() )
						if( l1[-1].id == -1 ):
							l2.append( l1[-1].getRecord() )
							il2.append(i)
						else:
							l3.append( l1[-1].getRecord() )
						i+=1

					ids = []
					if l2:
						ids = self.managers[rType].insertList( l2 );
					if l3:
						self.managers[rType].updateList( l3 );
					
					j = 0
					while j<len(ids):
						l1[ il2[j] ].id = ids[j] 
						j+=1
					
					self.ressources[rType].extend( l1 )	
			time.sleep( 1 );

class Saver( Thread ):
	def __init__(self, ressources={}, ressourceLock=None):
		Thread.__init__(self);
		self.ressources		= ressources
		self.ressourceLock	= ressourceLock
		
		self.handlers		= {}
		for k in rTypes:
			self.handlers[k]= rTypes[k][3]()
		
	def run(self):
		while True:
			ressource 	= None
			rType		= ""
			for key in self.ressources:
				while self.ressources[ key ] :
					with self.ressourceLock:
						if  self.ressources[ key ] :
							ressource = self.ressources[key].pop()
					if ressource != None :
						self.handlers[key].save( ressource ) 
				
			time.sleep( 1 )
				
class OverseerThread( Thread ):
	def __init__(self, masterAddress, useragent, cPort, maxWorkers, period, urls, contentTypes, delay, maxSavers):
		Thread.__init__(self)
		self.masterAddress	= masterAddress
		self.useragent		= useragent
		self.cPort			= cPort
		
		self.period			= period
		self.maxWorkers 	= maxWorkers
		
		self.workers 	= []
		self.aliveWorkers 	= 0
		
		self.newUrls		= []
		self.urls			= urls
		self.contentTypes	= contentTypes
		self.delay			= delay
		
		self.maxSavers		= maxSavers
		self.ressourceLock	= RLock()
		self.savers			= []
		
		self.urlsLock 		= RLock()
		self.sender			= UrlSender( self.masterAddress, self.cPort, self.newUrls )
		
		
		self.manager			= Url.UrlManager()
		
		self.con				= SQLFactory.getConn()
		self.managers			= {}
		self.waitingRessources	= [] #waiting for sql saving
		self.ressources			= {} #already save in sql, waiting for data saving
		
		for k in rTypes:
			self.managers[k]= rTypes[k][2]( self.con )
			self.ressources[k]= []
		
		self.sqlHandler		= SQLHandler( self.managers, 100, self.waitingRessources, self.ressources)
		
		
	def pruneWorkers(self):
		i=0
		while i<len(self.workers) :
			if not self.workers[i].is_alive():
				self.aliveWorkers -=1
				del self.workers[i]
			i+=1
	
	def harness(self):
		i=0
		while i<self.maxSavers:
			s =  Saver( self.ressources, self.ressourceLock )
			self.savers.append( s )
			s.start()
			i+=1
		
		self.sender.start()
		self.sqlHandler.start()
		j=0
		
		while True:
			minUrls = 2 * self.maxWorkers
			if len(self.urls) < minUrls:
				t = TcpClient( self.masterAddress, self.cPort )
				t.send( TcpMsg.T_PENDING )
			print( "newUrls        : ", sys.getsizeof( self.newUrls ) )
			print( "urls : ", sys.getsizeof( self.urls ) )
			print()
			while self.urls :
				#if len(self.urls) < minUrls:
					#t = TcpClient( self.masterAddress, self.cPort )
					#t.send( TcpMsg.T_PENDING )
				
				n = self.maxWorkers-self.aliveWorkers
				if n>0 :
					i=0
					while i<n :
						#try :
						w = WorkerThread( urlsLock=self.urlsLock, urls=self.urls, newUrls=self.newUrls,
											contentTypes=self.contentTypes, delay=self.delay, manager=self.manager,
											waitingRessources=self.waitingRessources )
						self.workers.append( w )
						self.aliveWorkers += 1
						w.start()
						i+=1
						#except Exception:
							#pass
						
				time.sleep( self.period ) 
				self.pruneWorkers()
			time.sleep( self.period ) 
		
	def run(self):
		self.harness()		

class Slave( TcpServer ):
	"""
		@param contentTypes 	- content types allowed ( {contentType = charset(def="", ie all charset allowed)})
	"""
	def __init__(self, masterAddress="", useragent="*", cPort=1645 , port=1646, period=10, maxWorkers=2, contentTypes={"*":False},
		delay=86400, maxSavers=1) :
		self.masterAddress	= masterAddress
		self.useragent		= useragent
		TcpServer.__init__(self, port)				 #server port
		self.cPort			= cPort
		
		self.period			= period
		
		self.maxWorkers 	= maxWorkers
		self.numberWorkers  = 0
		
		self.delay			= delay
		
		self.contentTypes	= contentTypes
		self.urls			= []
		
		self.maxSavers		= maxSavers
		t = TcpClient( masterAddress, self.cPort )
		t.send( TcpMsg.T_PENDING )
		
		self.initNetworking()
		self.overseer		= None
		
	def harness(self):
		self.overseer = OverseerThread(masterAddress = self.masterAddress, useragent = self.useragent, cPort = self.cPort,
										maxWorkers  = self.maxWorkers, period = self.period, urls = self.urls, 
										contentTypes=self.contentTypes, delay=self.delay, maxSavers=self.maxSavers)
		self.overseer.start()
		self.listen()
	
	### Network ###
	def process(self, type, data, address):
		if type == TcpMsg.T_DONE:
			pass
	
		if type == TcpMsg.T_URL_TRANSFER:
			self.addUrls( data )
			#if not self.overseer.is_alive():
				#self.overseer = OverseerThread(masterAddress = self.masterAddress, useragent = self.useragent, cPort = self.cPort,
												#maxWorkers  = self.maxWorkers, period = self.period, urls = self.urls,
												#contentTypes=self.contentTypes, delay=self.delay)
				#self.overseer.start()
	
	### CrawlerThread handling ###
	def addUrls(self, data ):
		self.urls.extend( Url.unserializeList( data ) )	
