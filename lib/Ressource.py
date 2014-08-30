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



class BaseModel(Model):
    """A base model that will use our MySQL database"""
    

import SQLFactory
import peewee
from peewee import *

class Record( Model ):
	"""
	"""
	id = peewee.BigIntegerField()
	url = peewee.TextField()
	domain = peewee.TextField()
	relatedRessources = peewee.TextField()
	size = peewee.TextField()
	contentType = peewee.TextField()
	time = peewee.TextField()
	md5 = peewee.TextField()
	chunk = peewee.TextField()
	lastUpdate = peewee.DateTimeField() 

	
	class Meta:
        database = db


class Ressource( Model ):
	
	
	
	def __init__(self):
		self.id = -1
		self.url = ""
		self.domain = ""
		self.relatedRessources = [] # [(type, id)]
		
		self.size = []
		self.contentType = []
		#self.revision = 0 #number of revision
		self.time = []
		self.md5 = []
		
		self.chunk = []
		self.lastUpdate = 0
	def save(self):
		
