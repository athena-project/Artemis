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
import peewee
import Ressource	
from contentTypeRules import *
#from Text import *
#from Ressource import *
#from Html import *
import hashlib


class WorkerThread( Thread ):
	def __init__(self, urlsLock=None, urls=[], newUrls=[], delay=86400):
		"""
		"""
		Thread.__init__(self)
		self.urlsLock			= urlsLock
		self.urls				= urls
		self.newUrls			= newUrls 
		self.delay				= delay
		self.manager 			= Url.UrlManager()
	
	def run(self):
		while True:
			with self.urlsLock:
				if not self.urls :
					return None
				url = self.urls.pop()
			#Sql check
			record = self.manager.getByUrl( url.url )
			if record == None:
				self.dispatch( url, record )
			elif record.lastVisited < time.time()-self.delay:
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
		t1 = time.time()
		r = request.urlopen( url.url)	
		print( time.time()-t1)
		#ContentType 
		cT = r.getheader("Content-Type")
		cTl=cT.split(";")
		
		contentType	= cTl[0].strip()
		charset		= "UTF-8"
		if len(cT)>1:
			charset = cTl[1].split("=")
			if len(charset)>1:
				charset	= charset[1].strip()
			else:
				charset = charset[0].strip()
		
		if( r.status == 200 ):
			if contentType not in contentTypeRules:
				#log
				pass
			else:
				ressourceManager	= contentTypeRules[ contentType ][1]()
				ressource 			= ressourceManager.getByUrl( url=url.url )
				t 					= time.time()
				data 				= r.read()
				print("marcher ")
				#Md5
				m_md5 = hashlib.md5()
				m_md5.update(data)
				h_md5 = m_md5.hexdigest()
				
				data				= data.decode(charset.lower())
				
				if ressource == None:
					ressource = contentTypeRules[ contentType ][0]()
					ressource.url					= url.url
					ressource.domain				= urlObj.netloc
					ressource.data					= data
				else:
					if h_md5 == ressource.md5[-1]:
						ressource.data				= data
					
					ressource.size.append( 			len(data ) )
					ressource.contentTypes.append( 	cT ) 
					ressource.times.append( 		time.time() )
					ressource.md5.append( 			h_md5  )
					ressource.lastUpdate			= t
				
				ressource.sizes.append(			len(data ) ) 
				ressource.contentTypes.append( 	cT ) 
				ressource.times.append( 		time.time() )
				ressource.md5.append(	 		h_md5  )
				ressource.lastUpdate			= t
					
				#url maj
				if urlRecord == None:
					urlRecord=Url.UrlRecord( protocol=urlObject.scheme, domain=urlObject.netloc, url=url.url )
				else:
					urlRecord.lastMd5		= h_md5
					urlRecord.lastVisited	= t
				
				self.manager.save(urlRecord)
				ressource.save()	
				
				#Feed the slave with the links owned by the current ressource
				self.newUrls.extend( ressource.extractUrls( urlObj ) )
		else:
			pass
			#log
	
	#def ftp( self, url):
	#	r = request.urlopen( url)	
	#	if( r.status == 200 ):
	#		
	#	else:
	#		#log
			
			
class OverseerThread( Thread ):
	def __init__(self, masterAddress, useragent, cPort, maxWorkers, period, urls, delay):
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
		self.delay			= delay
		
		self.urlsLock = RLock()
		
	def pruneWorkers(self):
		for worker in self.workers:
			if not worker.is_alive():
				self.aliveWorkers -=1
				del worker

	def makeBundleFromList(self, l):
		bundle = ""
		urlSize = 0
		for url in l:
			urlSize += url.size()
		i,n = 0, min( TcpMsg.T_URL_TRANSFER_SIZE, urlSize)
		 
		while i<n :
			tmp = urls.pop()
			if tmp.size + i >= n:
				i=n
				urls.append(tmp)
			else :	
				tmp	= Url.serialize( tmp )+"~" 
				i	+=tmp.size()
				bundle+=tmp
		
		return bundle
	
	def harness(self):
		if not self.urls:
				t = TcpClient( self.masterAddress, self.cPort )
				t.send( TcpMsg.T_PENDING )
				
		while self.urls :
			n = self.maxWorkers-self.aliveWorkers
			if n>0 :
				i=0
				while i<n :
					w = WorkerThread( urlsLock=self.urlsLock, urls=self.urls, newUrls=self.newUrls, delay=self.delay )
					self.workers.append( w )
					self.aliveWorkers += 1
					self.workers[ self.aliveWorkers-1 ].start()
					i+=1
			
			time.sleep( self.period ) 
			self.pruneWorkers()
		
		while self.newUrls:
			t = TcpClient( self.masterAddress, self.cPort )
			t.send( TcpMsg.T_URL_TRANSFER+makeBundleFromRecordList( self.newUrls ) )
	
	def run(self):
		self.harness()		
	

class Slave( TcpServer ):
	"""
	"""
	def __init__(self, masterAddress="", useragent="*", cPort=1645 , port=1646, period=10, maxWorkers=2, delay=86400) :
		self.masterAddress	= masterAddress
		self.useragent		= useragent
		TcpServer.__init__(self, port)				 #server port
		self.cPort			= cPort
		
		self.period			= period
		
		self.maxWorkers 	= maxWorkers
		self.numberWorkers  = 0
		
		self.delay			= delay
		
		self.urls			= []
		
		t = TcpClient( masterAddress, self.cPort )
		t.send( TcpMsg.T_PENDING )
		
		self.initNetworking()
		self.overseer		= None
		
	def harness(self):
		self.overseer = OverseerThread(masterAddress = self.masterAddress, useragent = self.useragent, cPort = self.cPort,
										maxWorkers  = self.maxWorkers, period = self.period, urls = self.urls, delay=self.delay)
		self.overseer.start()
		self.listen()
	
	### Network ###
	def process(self, type, data, address):
		if type == TcpMsg.T_DONE:
			pass
	
		if type == TcpMsg.T_URL_TRANSFER:
			self.addUrls( data )
			if not self.overseer.is_alive():
				self.overseer = OverseerThread(masterAddress = self.masterAddress, useragent = self.useragent, cPort = self.cPort,
												maxWorkers  = self.maxWorkers, period = self.period, urls = self.urls,
												delay=self.delay)
				self.overseer.start()
	
	### CrawlerThread handling ###
	def addUrls(self, data ):
		self.urls.extend( Url.unserializeList( data ) )	
