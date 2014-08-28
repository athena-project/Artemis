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
import pickle
import TcpMsg.py

class TcpClient:
	"""
	
	"""
	
	def __init__(self, h, p):
		self.lastMsg = 0;
		self.connected = False ;
		self.host = host;
		self.port = p;
		
	def __del__(self):
		self.deco()

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
	
	
	def initNetworking(self, i=10):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect( self.host, self.port )
		
		send( TcpMsg( TcpMsg.T_ID ) )
		if( !self.connected && i!=0 ):
			self.initNetworking(i-1)
		
	def send(self, msg)
		#Begin co
		self.lastMsg = msg
		self.sock.send( msg.serialize().encode() )
		
		#Waiting for server answer
		data = ""
		again = True
		while again:
			buffer = self.sock.recv( 4096 )
			data += buffer.decode()
			if data:
				again = True
			else:
				again = False
		
		self.process( data )
		
		#End 
		self.sock.send( TcpMsg( TcpMsg.T_DONE ).serialize().encode() )
	
		
	def deco(self):
		self.lastMsg = TcpMsg( TcpMsg.T_DECO ).serialize().encode()
		self.connection.send( self.lastMsg )
		self.connection.close()
	
