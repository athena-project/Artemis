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
	def __init__(self, urlsLock=None, urls=[], newUrls=[], contentTypes={"*":False}, delay=86400, manager=None):
		"""
		"""
		Thread.__init__(self)
		self.urlsLock			= urlsLock
		self.urls				= urls
		self.newUrls			= newUrls
		self.contentTypes		= contentTypes 
		self.delay				= delay
		self.manager 			= manager
	
	def run(self):
		while True:
			with self.urlsLock:
				if not self.urls :
					return None
				url = self.urls.pop()
			#Sql check
				record = self.manager.getByUrl( url.url )
			if record == None or (record.lastVisited < time.time()-self.delay):
				self.dispatch( url, record )
				
				
	### Network handling ###
	def dispatch(self, url, urlRecord):
		urlObject = urlparse( url.url )	
		if( urlObject.scheme == "http" or urlObject.scheme == "https"):
			self.http( url, urlObject, urlRecord )
		#if( urlObject.scheme == "ftp" or urlObject.scheme == "ftps"):
		#	self.ftp( url )
		else :
			pass
			#log
			
	def http( self, url, urlObj, urlRecord ):
		print("under way")
		try:
			r = request.urlopen( url.url )	
		except :
			#log
			return
		#ContentType 
		cT = r.getheader("Content-Type")

		#Statut check
		if( r.status != 200 ):
			return 
		try:
			self.save(url, urlObj, urlRecord, cT, r.read())
		except Exception as e:
			f=open("svae_slave.log", "a")
			f.write(str(e))#format( e.strerror))
			f.close()
		
	
	#def ftp( self, url):
	#	r = request.urlopen( url)	
	#	if( r.status == 200 ):
	#		
	#	else:
	#		#log
	
	def save(self, url, urlObj, urlRecord, cT, data):
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

		ressourceHandler	= contentTypeRules[ contentType ][1]
		ressourceRecord		= ressourceHandler.manager.getByUrl( url=url.url )
		ressource			= contentTypeRules[ contentType ][0]()
		ressource.hydrate( ressourceRecord )
		t 					= time.time()

		#Hash
		m_sha512 = hashlib.sha512()
		m_sha512.update(data)
		h_sha512 = m_sha512.hexdigest()
		
		data				= str(data.decode(charset.lower()))

		#UrlRecord hydrating
		if urlRecord == None:
			urlRecord=Url.UrlRecord( protocol=urlObj.scheme, domain=urlObj.netloc, url=url.url )
		urlRecord.lastsha512		= h_sha512
		urlRecord.lastVisited	= t
	
		self.manager.save( urlRecord )
		
		#hash traitement
		#à faire
		

		#Ressource hydrating
		ressource.url					= url.url
		ressource.domain				= urlObj.netloc
		ressource.sizes.append(			len(data ) ) 
		ressource.contentTypes.append( 	cT ) 
		ressource.times.append( 		time.time() )
		ressource.sha512.append(	 		h_sha512  )
		ressource.lastUpdate			= t
		if h_sha512 == ressource.sha512[-1]:
			ressource.data				= data
	
		ressourceHandler.save( ressource )	
		
		#Feed the slave with the links owned by the current ressource
		self.newUrls.extend( ressource.extractUrls( urlObj ) )
		t = time.time()-t
		print(t)
		
class UrlSender( Thread ):
	def __init__(self, masterAddress, cPort, newUrls):
		Thread.__init__(self)
		self.masterAddress	= masterAddress
		self.cPort			= cPort
		self.newUrls		= newUrls
	
	def run(self):
		while True:
			if self.newUrls :
				print("sending")
				t = TcpClient( self.masterAddress, self.cPort )
				t.send( TcpMsg.T_URL_TRANSFER + 
					Url.makeBundle( self.newUrls, TcpMsg.T_URL_TRANSFER_SIZE-TcpMsg.T_TYPE_SIZE ) )
			time.sleep(1.5)
							
		
class OverseerThread( Thread ):
	def __init__(self, masterAddress, useragent, cPort, maxWorkers, period, urls, contentTypes, delay):
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
		
		self.urlsLock 		= RLock()
		self.sender			= UrlSender( self.masterAddress, self.cPort, self.newUrls )
		
		self.manager		= Url.UrlManager()
		
	def pruneWorkers(self):
		for worker in self.workers:
			if not worker.is_alive():
				self.aliveWorkers -=1
				del worker
	
	
	def harness(self):
		self.sender.start()
		j=0
		
		while True:
			if not self.urls:
				t = TcpClient( self.masterAddress, self.cPort )
				t.send( TcpMsg.T_PENDING )
			while self.urls :
				n = self.maxWorkers-self.aliveWorkers
				if n>0 :
					i=0
					print("nbr connexion here j"+str(j))
					while i<n :
						j+1
						#try :
						w = WorkerThread( urlsLock=self.urlsLock, urls=self.urls, newUrls=self.newUrls,
											contentTypes=self.contentTypes, delay=self.delay, manager=self.manager )
						self.workers.append( w )
						self.aliveWorkers += 1
						w.start()
						i+=1
						j+=1
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
	def __init__(self, masterAddress="", useragent="*", cPort=1645 , port=1646, period=10, maxWorkers=2, contentTypes={"*":False}, delay=86400) :
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
		
		t = TcpClient( masterAddress, self.cPort )
		t.send( TcpMsg.T_PENDING )
		
		self.initNetworking()
		self.overseer		= None
		
	def harness(self):
		self.overseer = OverseerThread(masterAddress = self.masterAddress, useragent = self.useragent, cPort = self.cPort,
										maxWorkers  = self.maxWorkers, period = self.period, urls = self.urls, 
										contentTypes=self.contentTypes, delay=self.delay)
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
