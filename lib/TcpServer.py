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
#	@author Severus21
#
import select
import socket
import sys



import time

import socket
import select
from TcpMsg import TcpMsg

class TcpServer:
	def __init__(self, port):
		"""
			@param	port	- port to listen
		"""
		self.sock = None
		self.clientsConnected = []
		self.port = port
		self.host = ''#socket.gethostname()
		
	def __del__(self):
		for client in self.clientsConnected:
			client.close()
	
	def initNetworking(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setblocking(0)
		self.sock.bind( (self.host, self.port) )
		self.sock.listen( 5 )	
		
		
	
	def listen(self): # http://pymotw.com/2/select/
		# Sockets from which we expect to read
		inputs = [ self.sock ]

		# Sockets to which we expect to write
		outputs = [ ]
		
		while inputs:
			# Wait for at least one of the sockets to be ready for processing
			readable, writable, exceptional = select.select(inputs, outputs, inputs)	
			
			# Handle inputs
			for s in readable:

				if s is self.sock:
					# A "readable" server socket is ready to accept a connection
					connection, client_address = s.accept()
					connection.setblocking(0)
					inputs.append(connection)

				else:
					buff = s.recv(TcpMsg.T_BUFFER_SIZE)
					if buff:
						# A readable client socket has data
						# Add output channel for response
						if s not in outputs:
							outputs.append(s)	
						
						#data=""
						#while buff:
							#data+=buff.decode('utf-8')
							#buff = s.recv(1024)
						data=buff.decode('utf-8')

						self.process( data[:TcpMsg.T_TYPE_SIZE], data[TcpMsg.T_TYPE_SIZE:], s.getpeername() )
					else:
						# Interpret empty result as closed connection
						# Stop listening for input on the connection
						if s in outputs:
							outputs.remove(s)
						inputs.remove(s)
						s.close()
					
			# Handle outputs
			for s in writable:
				pass
					
			# Handle "exceptional conditions"
			for s in exceptional:
				# Stop listening for input on the connection
				inputs.remove(s)
				if s in outputs:
					outputs.remove(s)
				s.close()
					
	def process(self, type, data, address):
		pass
