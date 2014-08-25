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
		self.lastMsg = 0
		self.lients = []
		self.port = p
		self.host = ""
		
	def __del__(self):
		sed.deco()
	
	def initNetworking(self):
		self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connection.bind( self.host, self.port )
		selt.connection.listen( 15 )

		
	def listen(self):
		connexions_demandees, wlist, xlist = select.select([connexion_principale],[], [], 1)
	
