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
		sed.deco()
	
	def initNetworking(self):
		self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connection.connect( self.host, self.port )
		
		#Begin co
		self.lastMsg = TcpMsg( TcpMsg.T_ID ).serialize().encode()
		self.connection.send( self.lastMsg )
		
		#Waiting for server answer
		data = ""
		again = True
		while again:
			buffer = self.connection.recv( 4096 )
			data += buffer.decode()
			if data:
				again = True
			else:
				again = False
		
		msg = pickle.load( data )
		assert isinstance(msg, TcpMsg)
		if msg.type != TcpMsg.T_ACCEPTED:
			raise "bad type msg"
		
		#End co
		self.lastMsg = TcpMsg( TcpMsg.T_DONE ).serialize().encode()
		self.connection.send( self.lastMsg )
		
	def deco(self):
		self.lastMsg = TcpMsg( TcpMsg.T_DECO ).serialize().encode()
		self.connection.send( self.lastMsg )
		self.connection.close()
	
