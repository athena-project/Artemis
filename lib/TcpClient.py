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

import socket
import time
from TcpMsg import TcpMsg

class TcpClient:
	"""
	
	"""
	
	def __init__(self, h, p):
		self.sock = None
		self.lastMsg = None;
		self.connected = False ;
		self.host = h;
		self.port = p;
		
		
	def __del__(self):
		pass
		#self.initNetworking()
		#self.sock.send( TcpMsg.T_DECO.encode() )
		#self.sock.close()

	# A surcharger, virtual
	def getUrls(self, msg):
		pass
	
	#Data is a string , for child class
	def process(self, data):
		msg = pickle.load( data )
		assert isinstance(msg, TcpMsg)
		
		if msg.type == TcpMsg.T_ACCEPTED:
			self.connected = True
		if msg.type == TcpMsg.T_DONE:
			pass
		if msg.type == TcpMsg.T_RESEND:
			self.send( self.lastMsg ) 
		if msg.type == TcpMsg.T_URL_TRANSFER:
			self.getUrls( msg )
	
	
	def initNetworking(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect( (self.host, self.port) )
		
	def send(self, msg):
		#Begin 
		self.initNetworking()
		self.lastMsg = msg
		self.sock.sendall( msg.encode() )
		self.sock.close()
		
		#End 
		#self.initNetworking()
		#self.sock.send(  TcpMsg.T_DONE.encode() )
		#self.sock.close()
