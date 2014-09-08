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
	
	
	def __init(self ) :
	
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
