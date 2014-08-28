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
import select
import TcpMsg.py

class TcpServer:
	"""
	
	"""
	
	def __init__(self, p):
		self.clientsConnected = []
		self.clientsAvailable = []
		self.port = p
		self.host = socket.gethostname()
		
	def __del__(self):
		for client in self.clientsConnected:
			client.close()

		sock.close()	
	
	def initNetworking(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind( self.host, self.port )
		selt.sock.listen( 15 )
		
	# A surcharger, virtual
	def getUrls(self, msg):
		pass	
	
	#Data is a string , for child class
	def process(self, data, i):
		msg = pickle.load( data )
		if msg.type == TcpMsg.T_DONE:
			pass
		if msg.type == TcpMsg.T_DECO:
			client.close()
			self.clientConnected.pop( [i] )
		if msg.type == Tcp.T_ID:
			self.send( TcpMsg( TcpMsg.T_ACCEPTED ), self.ready_to_write[i] )
		if msg.type == TcpMsg.T_PENDING && self.clientAvailable.count(i) == 0:
			self.clientsAvailable.append( i )
		if msg.type == TcpMsg.T_PROCESSING:
			self.clientsAvailable.remove( i )
		if msg.type == TcpMsg.T_URL_TRANSFER:
			self.getUrls(msg)
	
	def send(self, tmpSock, msg)
		self.tmpSock.send( msg.serialize().encode() )
		
	
	
	
	def listen(self):
		while True :
			connectionRequested, wlist, xlist = select.select([sock],[], [], 60)
			
			for connexion in connectionRequested:
				connexion_avec_client, infos_connexion = connexion.accept()
				# On ajoute le socket connecté à la liste des clients
				slef.clientsConnected.append(connexion_avec_client)
				
			ready_to_read = []
			try:
				self.ready_to_read, self.ready_to_write, self.in_error = select.select( self.clientsConnected, [], [], 60)
			except select.error:
				pass
			else:
				i = 0
				# On parcourt la liste des clients à lire
				for client in self.ready_to_read:
					data = ""
					again = True
					while again:
						buffer = self.connection.recv( 4096 )
						data += buffer.decode()
						if data:
							again = True
						else:
							again = False
					self.process( data, i )
					i++
					
		
		
