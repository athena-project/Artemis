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
import SQLFactory
from Text import *
import html.parser 
from urllib.parse import urlparse


class HTMLParser( html.parser.HTMLParser ):
	"""
	"""
	def __init__(self, parentUrl):
		html.parser.HTMLParser.__init__(self)
		self.relatedRessources 	 	= []
		self.parentUrl			   	= parentUrl
		
	def handle_starttag(self, tag, attrs):
		if( tag != 'a' and tag != 'img' and tag != 'link' and tag != 'script' and tag != 'source' ):
			return None
		
		url = ""
		ctype = ""
		charset = ""
		alt = ""
		
		for (name,value) in attrs :
			if(name == 'href' or name =='download' or name== 'src'):
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
				url = self.parentUrl.scheme+"://"+self.parentUrl.netloc
			else:
				url = self.parentUrl.scheme+"://"+t2.netloc
		else :
			url = t2.scheme+"://"+t2.netloc
			
		url += t2.path 
		if t2.query :
			url+="?"+t2.query

		tmp = Url.Url(url, o=tag, t=ctype, charset=charset, alt=alt)
		self.relatedRessources.append( tmp )

class HtmlManager(TextManager):
	def __init__(self):
		TextManager.__init__(self)
		self.table		= "html"

class HtmlRecord( TextRecord ):
	def __init__(self):
		TextRecord.__init__(self)
		
class HtmlHandler( TextHandler ):
	def __init__(self, manager):
		TextHandler.__init__(self, manager)
		
class Html( Text ):
	"""
	"""
	
	def __init__(self):
		Text.__init__(self)
	
	def extractUrls(self, parentUrl):
		p = HTMLParser(parentUrl)
		p.feed( self.data )
		p.close()
		return p.relatedRessources
		
		
	
	
