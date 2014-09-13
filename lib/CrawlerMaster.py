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
from urllib.parse import urlparse
from TcpServer import TcpServer
from TcpClient import TcpClient
import UrlCacheHandler
import RobotCacheHandler

class CrawlerMaster( TcpServer ):
	"""
	"""
	
	
	def __init__(self, useragent="*", contentTypes=[], domainRules={"*":True}, protocolRules={"*":True}, sourceRules={"*":True} urlsPerSlave=10) :
		"""
			@param contentTypes 	- content types allowed ( {contentType = charset(def="", ie all charset allowed)})
			@domainRules			- domain => true ie allowed False forbiden *=>all
			@param maxMemRobots		- maximun of robot.txt ept in disk cache
			@param urlsPerSlave		- 
		"""
		self.useragent 			= useragent
		
		self.contentTypes 		= contentTypes
		self.domainRules		= domainRules
		self.protocolRules		= protocolRules
		self.sourceRules		= sourceRules
		self.maxSizeSlave		= maxSizeSlave # size max by msg
		
		self.slavesAvailable 	= [] # [address_ip1, address_ip2..]
		
		self.urlCacheHandler	= UrlCacheHandler.UrlCacheHandler()
		self.robotCacheHandler	= RobotCacheHandler.RobotCacheHandler()		
	
	### Network ###
	def process(self, data, address):
		if msg.type == TcpMsg.T_DONE:
			pass
			
		if msg.type == TcpMsg.T_DECO:
			self.slavesAvailable.remove( address )
			
		if msg.type == Tcp.T_ID & self.clientAvailable.count(address) == 0:
			self.append.remove( address )
			t = TcpClient.TcpClient( "", 1646 )
			t.send( TcpMsg.T_ACCEPTED )
			
		if msg.type == TcpMsg.T_PENDING & self.clientAvailable.count(address) == 0:
			self.clientsAvailable.append( i )
			
		if msg.type == TcpMsg.T_PROCESSING:
			self.slavesAvailable.remove( address )
			
		if msg.type == TcpMsg.T_URL_TRANSFER:
			self.addUrls( data )
	
	
	### Url Handling ###
	def validUrl(self, url):
		#Check in ram
		if( self.urlCacheHandler.exists( url ) )
			return False
		
		#Chek source
		if url.source in self.sourceRules:
			if !self.sourceRules[urlP.source]:
				return False
		else:
			return False
			
		#Check domain and protocol
		urlP = urlparse( url.url )
		
		if urlP.sheme in self.protocolRules:
		  if !self.protocolRules[urlP.sheme]:
			  False
		else :
			if !self.protocolRules["*"]:
				return False
		
		if urlP.netloc in self.domainRules:
		  if !self.domainRules[urlP.netloc]:
			  False
		else :
			if !self.domainRules["*"]:
				return False
		
		#Robot check
		robot = self.robotCacheHandler.get( url )
		if !robot.can_fetch(self.useragent , url.url):
			return False
			
		#Sql check
		try:
			UrlRecord.get( UrlRecord.url == elmt.url )
		except peewee.UrlRecordDoesNotExists:
			return False
			
		return True
			
	def addUrls(self, urls ):
		for url in urls :
			self.urlCacheHandler.add( url ) if self.validUrl( url ) else pass
	
	def makeBundle(self):
		bundle = ""
		urlSize = self.urlCacheHandler.currentRamSize + self.urlCacheHandler.currentMemSize
		i,n = 0,0
		
		if urlSize < self.slavesAvailable * self.maxSizeSlave :
			n = urlSize % self.slavesAvailable + 1 
		else
			n = self.maxSizeSlave
		
		while i<n:
			tmp = self.urlCacheHandler.get()
			if tmp.size + i >= n:
				while i<n:
					bundle+=" " 
					i+=1
					
			tmp	= Url.serialize( tmp )+"~" 
			i	+=tmp.size()
			bundle+=tmp
		
		return bundle
		
	
