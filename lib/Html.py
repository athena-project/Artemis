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

import Url
from Text import Text
import html.parser 
from urllib.parse import urlparse


class HTMLParser( html.parser ):
	"""
	"""
	def __init__(self):
		html.parser.__init__(self, p)
		self.relatedRessources = []
		self.urlObj = urlparse(p)
		
	def handle_starttag(self, tag, attrs):
		if( tag != 'a' && tag != 'img' && tag != 'link' && tag != 'script' && tag != 'source' ):
			pass
		
		url = ""
		ctype = ""
		charset = ""
		alt = ""
		
		for (name,value) in attrs :
			if(name == 'href' | name =='download' | name== 'src'):
				url = value
			if name == 'alt':
				alt = value
			if name == 'charset':
				charset = value
			if name == 'type':
				ctype = value
				
		t2 = urlparse( url )
		
		if( t2.scheme =='' ):
			if( t2.netloc == '' ):
				url = self.urlObj.scheme+"://"+self.urlObj.path+"/"+url
			else:
				url = self.urlObj.scheme+"://"+url
			

		tmp = Url(tag, url, ctype, charset, alt)
		self.relatedRessources.append( tmp )

class Html( Text ):
	"""
	"""
	
	def __init__(self):
		parent.__init__(self)
	
	def extractRelatedRessources(self):
		p = HTMLParser()
		p.feed( self.data )
		p.close()
		return p.relatedRessources
		
		
	
	
