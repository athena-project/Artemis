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

from threading import Thread
from urllib.request as request
from urllib.parse import urlparse

class CrawlerThread( Thread ):
	"""
	"""

	def __ini__(self, contentTypeRules): 
		
		self.contentTypeRules = contentTypeRules
		self.urls = []
		self.newUrls = [] 
		
	def dispatch(self, url):
		urlObject = urlparse( url )	
		if( urlObject.scheme == "http" or urlObject.scheme == "https"):
			self.http( url )
		else if( urlObject.scheme == "ftp" or urlObject.scheme == "ftps"):
			self.ftp( url )
		else :
			#log
			
	def http( self, url ):
		r = request.urlopen( url)	
		if( r.status == 200 ):
			
		else:
			#log
	
	def ftp( self, url):
		r = request.urlopen( url)	
		if( r.status == 200 ):
			
		else:
			#log
