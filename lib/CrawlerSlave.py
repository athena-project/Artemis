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

from TcpServer import TcpServer
from TcpClient import TcpClient

class CrawlerSlave( TcpServer ):
	"""
	"""
	
	
	def __init(self, maxThreads=2, threadUrls=100 ) :
		self.maxThreads 	= maxThreads
		self.threadUrls		= threadUrls
		self.numberThreads  = 0
		
		self.urls			= []
		self.newUrls		= []
		
		self.threads		= []
		self.aliveThreads 	= 0
		
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
			self.
			self.slavesAvailable.remove( address )
			
		if msg.type == TcpMsg.T_URL_TRANSFER:
			self.
	
	### CrawlerThread handling ###
	
	def harness(self):
		if self.urls == 0:
			on demande de nouveau truc 
			
		n = self.maxThreads-self.aliveThreads
		if n>0 :
			i,m = 0, min( len( self.urls ) // n + 1, self.threadUrls)
			while i<n :
				j,l=0,[]
				while j<m:
					l.append( self.urls.pop() )
					j+=1
					
				self.threads.append( CrawlerSlave( l ) )
				self.aliveThreads += 1
				self.threads[ self.aliveThreads-1 ].start()
				i+=1
			
			
