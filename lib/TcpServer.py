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
import select
from TcpMsg import TcpMsg

class TcpServer:
	"""
	
	"""
	
	def __init__(self, port):
		self.sock = None
		self.clientsConnected = []
		self.port = port
		self.host = ''#socket.gethostname()
		
	def __del__(self):
		for client in self.clientsConnected:
			client.close()
	
	def initNetworking(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind( (self.host, self.port) )
		self.sock.listen( 5 )	
	
	#Data is a string
	def process(self, type, data, address):
		pass

	def listen(self):
		while True :
			connectionRequested, wlist, xlist = select.select([self.sock],[], [], 60)
			
			for connexion in connectionRequested:
				connexion_avec_client, infos_connexion = connexion.accept()
				# On ajoute le socket connecté à la liste des clients
				self.clientsConnected.append(connexion_avec_client)
				
			self.ready_to_read, self.ready_to_write, self.in_error = [], [], []
			try:
				self.ready_to_read, self.ready_to_write, self.in_error = select.select( self.clientsConnected, [], [], 60)
			except select.error:
				pass
			else:
				i = 0
				# On parcourt la liste des clients à lire
				for client in self.ready_to_read:
					buffer = client.recv( 4096 )
					data = buffer.decode()
					j, size= 4096, TcpMsg.getSize( data )
					
					if not len( buffer ):	
						client.close()
						if( len(self.clientsConnected) > 0 ):
							self.clientsConnected.pop( i )
					else:	
						while j<size:
							buffer = client.recv( 4096 )
							data += buffer.decode()
							j+=4096
												
						self.process( data[:TcpMsg.T_TYPE_SIZE], data[TcpMsg.T_TYPE_SIZE:], client.getpeername() )
					i+=1
