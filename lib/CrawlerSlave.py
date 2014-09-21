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

import hashlib


class WorkerThread( Thread ):
	def __init(self, urls, newUrls, contentTypeRules):
		"""
			contentTypeRules		- contentType => Ressource type
		"""
		Thread.__init__(self)
		
		self.contentTypeRules	= contentTypeRules
		self.urls				= urls
		self.newUrls			= newUrls 
	
	def run(self):
		while True:
			with urlsLock:
				if not self.urls :
					return None
				url = self.urls.pop()
			
			#Sql check
			allowed = False
			try:
				record = UrlRecord.get( UrlRecord.url == elmt.url )
				if record.lastVisited <time.time()-self.delay:
					allowed = True
			except peewee.UrlRecordDoesNotExists:
				allowed = True
			
			if allowed:
				data = dispatch( url )
	
	### Network handling ###
	def dispatch(self, url):
		urlObject = urlparse( url )	
		if( urlObject.scheme == "http" or urlObject.scheme == "https"):
			self.http( url )
		#if( urlObject.scheme == "ftp" or urlObject.scheme == "ftps"):
		#	self.ftp( url )
		else :
			pass
			#log
			
	def http( self, url ):
		r = request.urlopen( url)	
		cT = r.getheader("Content-Type")
		if( r.status == 200 ):
			if None == cT or (cT not in self.contentTypeRules):
				#log
				pass
			else:
				#Md5
				m_md5 = hashlib.md5()
				m_md5.update(key)
				h_md5 = m_md5.hexdigest()
				
				ressource = contentTypesRules[cT].getByUrl( url )
				if ressource == None:
					ressource = self.contentTypesRules[cT]()
					ressource.url					= url
					ressource.domain				= urlparse( url ).netloc
					ressource.sizes.append(			len(r.data ) ) 
					ressource.contentTypes.append( 	cT ) 
					ressource.times.append( 		time.time() )
					ressource.md5.append(	 		h_md5  )
					ressource.lastUpdate			= time.time()
					ressource.data					= r.data
				else:
					if h_md5 == ressource.md5[-1]:
						ressource.data					= r.data
					
					ressource.size.append( 			len(r.data ) )
					ressource.contentTypes.append( 	cT ) 
					ressource.times.append( 		time.time() )
					ressource.md5.append( 			h_md5  )
					ressource.lastUpdate			= time.time()
					
				ressource.save()	
					
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
	def __init__(self, useragent, cPort, maxThreads, period, urls):
		Thread.__init__(self)
		self.useragent		= useragent
		self.cPort			= cPort
		
		self.period			= period
		self.maxWorkers 	= maxThreads
		
		self.workers 	= []
		self.aliveWorkers 	= 0
		
		self.newUrls		= []
		self.urls			= urls
		
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
				t = TcpClient.TcpClient( masterAddress, self.cPort )
				t.send( TcpMsg.T_PENDING )
				
		while self.urls :
			n = self.maxWorkers-self.aliveWorkers
			if n>0 :
				i=0
				while i<n :
					self.threads.append( CrawlerSlave( self.urls, self.newUrls ) )
					self.aliveWorkers += 1
					self.workers[ self.aliveWorkers-1 ].start()
					i+=1
			
			time.sleep( self.period ) 
			self.pruneWorkers()
		
		while self.newUrls:
			t = TcpClient.TcpClient( masterAddress, self.cPort )
			t.send( TcpMsg.T_URL_TRANSFER+makeBundleFromRecordList( self.newUrls ) )
	
	def run(self):
		self.harness()		
	

class Slave( TcpServer ):
	"""
	"""
	def __init__(self, masterAddress="", useragent="*", cPort=1645 , port=1646, period=10, maxThreads=2, threadUrls=100 ) :
		self.useragent		= useragent
		TcpServer.__init__(self, port)				 #server port
		self.cPort			= cPort
		
		self.period			= period
		
		self.maxThreads 	= maxThreads
		self.threadUrls		= threadUrls
		self.numberThreads  = 0
		
		self.urls			= []
		
		t = TcpClient( masterAddress, self.cPort )
		t.send( TcpMsg.T_PENDING )
		
	def harness(self):
		overseer = OverseerThread(useragent = self.useragent, cPort = self.cPort, maxThreads  = self.maxThreads,
										period = self.period, urls = self.urls
										)
		overseer.start()
		self.listen()
	
	### Network ###
	def process(self, data, address):
		if msg.type == TcpMsg.T_DONE:
			pass
	
		if msg.type == TcpMsg.T_URL_TRANSFER:
			self.addUrls( data )
	
	### CrawlerThread handling ###
	
	def addUrls(self, data ):
		self.urls.extend( Url.unserializeList( data[1:] ) )	
