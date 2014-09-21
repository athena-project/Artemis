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

import time
from urllib.parse import urlparse
from TcpServer import TcpServer
from TcpClient import TcpClient
from TcpMsg    import TcpMsg
import UrlCacheHandler
import RobotCacheHandler
from threading import Thread, RLock




class MasterThread( Thread ):
	ACTION_CRAWL	= 0
	ACTION_UPDATE	= 1
	def __init__(self, action, cPort, slavesAvailable, urlCacheHandler, period, nSqlUrls, nMemUrls ):
		Thread.__init__(self)
		
		
		self.action				= action 
		self.slavesAvailable	= slavesAvailable
		self.cPort				= cPort
	
		self.urlCacheHandler	= urlCacheHandler
		
		self.nSqlUrls			= nSqlUrls
		self.nMemUrls			= nMemUrls
		self.period				= period
		
	def makeBundle(self):
		bundle = ""
		urlSize = self.urlCacheHandler.currentRamSize + self.urlCacheHandler.currentMemSize
		i,n = 0,0
		
		if urlSize < TcpMsg.T_URL_TRANSFER_SIZE :
			n = urlSize
		else:
			n = TcpMsg.T_URL_TRANSFER_SIZE
		
		while i<n :
			tmp = self.urlCacheHandler.get()
			if tmp.size + i >= n:
				i=n
				self.urlCacheHandler.add(tmp)
			else :	
				tmp	= Url.serialize( tmp )+"~" 
				i	+=tmp.size()
				bundle+=tmp
		
		return bundle
		
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
	
	def crawl(self):
		while True:
			for slaveAdress in self.slavesAvailable:
				t = TcpClient.TcpClient( slaveAdress, self.cPort )
				t = TcpClient.TcpClient( slaveAdress, self.cPort )
				t.send( TcpMsg.T_URL_TRANSFER+makeBundle() )
				self.slavesAvailable.remove( slave )
			time.sleep( self.period )

	#def update(self):
		#query = ( UrlRecord.select().
				#where( UrlRecord.lastVisited < time.time()-self.delay  ).
				#order_by( UrlRecord.id).
				#paginate(1, self.nSqlUrls)
			   #)
			  
		#urls = Url.recordList2list( query.get() )
		#i = 0
		
		#while urls | (not self.urlCacheHandler.empty()) :
			#for slave in self.slavesAvailable:
				#if urls :
					#bundle = self.makeBundleFromRecordList( urls )
				#else:
					#bundle = self.makeBundle()
					#i+=
					
				#t = TcpClient.TcpClient( slave, self.cPort )
				#t.send( TcpMsg.T_URL_TRANSFER+bundle )
				#self.slavesAvailable.remove( slave )
				
				#if i>self.nMemUrls :
					#i=0
					#urls = Url.recordList2list( query.get() )
			#sleep( self.period )
	
	def run(self):
		if self.action == MasterThread.ACTION_CRAWL:
			self.crawl()
		if self.action == MasterThread.ACTION_UPDATE:
			self.update()
		

class Master( TcpServer ):
	"""
	"""
	
	
	def __init__(self, useragent="*", cPort=1646 , port=1645, period=10, contentTypes={"*":False}, domainRules={"*":False}, protocolRules={"*":False}, sourceRules={"*":False}, delay = 36000, nSqlUrls=100, nMemUrls=100) :
		"""
			@param contentTypes 	- content types allowed ( {contentType = charset(def="", ie all charset allowed)})
			@domainRules			- domain => true ie allowed False forbiden *=>all
			@param maxMemRobots		- maximun of robot.txt ept in disk cache
			@param urlsPerSlave		- 
		"""
		self.cPort				= cPort #client port
		TcpServer.__init__(self, port)				 #server port
		
		self.useragent 			= useragent
		self.period				= period # delay(second) betwen two crawl
		
		
		self.slavesAvailable	= [] #address1,..
		
		self.contentTypes 		= contentTypes
		self.domainRules		= domainRules
		self.protocolRules		= protocolRules
		self.sourceRules		= sourceRules
		
		self.delay				= delay # de maj
		self.nSqlUrls			= nSqlUrls#number of sql url per update block
		self.nMemUrls			= nMemUrls
		
		self.urlCacheHandler	= UrlCacheHandler.UrlCacheHandler()
		self.robotCacheHandler	= RobotCacheHandler.RobotCacheHandler()		
		
		self.initNetworking()
	
	def crawl(self):
		master = MasterThread( action = MasterThread.ACTION_CRAWL, cPort = self.cPort,
								slavesAvailable = self.slavesAvailable, urlCacheHandler = self.urlCacheHandler,
								period = self.period, nSqlUrls = self.nSqlUrls, nMemUrls = self.nMemUrls)
		master.start()
		self.listen()

	def update(self):
		master = MasterThread( action = MasterThread.ACTION_UPDATE, cPort = self.cPort,
								slavesAvailable = self.slavesAvailable, urlCacheHandler = self.urlCacheHandler,
								period = self.period, nSqlUrls = self.nSqlUrls, nMemUrls = self.nMemUrls)
		master.start()
		
		self.listen()
		
	### Network ###
	def process(self, data, address):
		if msg.type == TcpMsg.T_DONE:
			pass
			
		if msg.type == TcpMsg.T_PENDING:
			self.slavesAvailable.append( address )
			
		if msg.type == TcpMsg.T_URL_TRANSFER:
			self.addUrls( data )
	
	
	### Url Handling ###
	def validUrl(self, url):
		#Check in ram
		if( self.urlCacheHandler.exists( url ) ):
			return False
		
		#Chek source
		if url.source in self.sourceRules:
			if not self.sourceRules[urlP.source]:
				return False
		else:
			return False
			
		#Chek contentType
		if url.t in self.contentTypes:
			if not self.contentTypes[urlP.t]:
				return False
		else:
			if not self.contentTypes["*"]:
				return False
			
		#Check domain and protocol
		urlP = urlparse( url.url )
		
		if urlP.sheme in self.protocolRules:
		  if not self.protocolRules[urlP.sheme]:
			  False
		elif not self.protocolRules["*"]:
				return False
		
		if urlP.netloc in self.domainRules:
		  if not self.domainRules[urlP.netloc]:
			  False
		elif not self.domainRules["*"]:
				return False
		
		#Robot check
		robot = self.robotCacheHandler.get( url )
		if not robot.can_fetch(self.useragent , url.url):
			return False
			
		return True
			
	def addUrls(self, data ):
		urls = Url.unserializeList( data[1:] )
		for url in urls :
			if self.validUrl( url ):
				self.urlCacheHandler.add( url ) 
			else:
				pass
				
