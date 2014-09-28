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

import SQLFactory

import Ressource
import Text
import Html

R_TYPE_RESSOURCE	= "00"
R_TYPE_TEXT			= "1t"
R_TYPE_HTML			= "2h"

class HashManager:
	def __init__(self):
		self.con = SQLFactory.getConn()
		
	def __del__(self):
		self.con.close()
		
	def getByHash(self, hash):
		cur = self.con.cursor()
		cur.execute("SELECT * FROM "+self.table+" WHERE hash='"+hash+"'")

		r=None
		for row in cur: #url is a unique id
			r=RessourceRecord( row[0], row[1], row[2] )
		cur.close()
		
		return r
	
	def insert(self, record):
		cur = self.con.cursor()
		cur.execute("INSERT INTO hash (hash, rType) VALUES ('"+record.hash+"', '"+record.rType+"' )")
		self.con.commit()
		id = cur.lastrowid
		cur.close()
		return id

class HashRecord:
	"""
	"""
	def __init__(self, id=-1, hash="", rType=R_TYPE_RESSOURCE):
		"""
			@param rType	- type de la ressource(text, html, etc..) chaine de deux octets
		"""
		self.id 				= int(id)
		self.hash 				= hash
		self.rType 				= rType
