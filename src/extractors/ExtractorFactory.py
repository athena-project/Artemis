from hermes.Directory import Directory
from artemis.Task import TaskNature, buildFromURIs
from lxml import html,etree
from urllib.parse import urlparse
from io import StringIO, BytesIO
import sys

def init_extractor(ressource, task):
	if ressource._metadata["contentType"] == "text/html" : 
		return HTMLExtractor(ressource, task)
	elif type(ressource) == Directory :
		return DirectoryExtractor(ressource, task)
	elif task.nature == TaskNature.web_static_sitemap:
		return SitemapExtractor(ressource, task)
	else:
		return None 

class Extractor :
	def __init__(self, ressource, task):
		self.ressource	= ressource
		self.task		= task
	
	def extract(self, tmp):
		return []
 
class XMLExtractor(Extractor) :
	_balises	= [] #(balise, args), if args == "" then text child
	def __init__(self, ressource, task):
		self.ressource	= ressource
		self.task		= task
	
	def build_doc(self, tmp):
		return etree.parse(tmp, base_url=self.task.url)
	
	def extract(self, tmp):
		last	= tmp.tell()
		tmp.seek(0)
		
		raw_urls = []
		doc = self.build_doc( tmp )
		for balise, arg in self._balises:
			xpath = ''.join( ["//*[local-name() = '", balise, "']"] )
			if arg :
				xpath = ''.join([xpath, '/@', arg] )
			else:
				xpath = ''.join( [xpath, '/text()[1]'] )
			raw_urls.extend( doc.xpath(xpath) )

		collected_urls = []
		for url in raw_urls:
			t2 = urlparse( url )

			if( t2.scheme =='' ):
				if( t2.netloc == '' ):
					url = self.task.scheme+"://"+self.task.netloc
				else:
					url = self.task.scheme+"://"+t2.netloc
			else :
				url = t2.scheme+"://"+t2.netloc
				
			url += t2.path 
			if t2.query :
				url+="?"+t2.query
				
			collected_urls.append( url )
		
		tmp.seek( last )
		return buildFromURIs( collected_urls )		

class SitemapExtractor(XMLExtractor) :
	_balises	= [ ("loc", "") ]
	
	def __init__(self, ressource, task):
		self.ressource	= ressource
		self.task		= task

class HTMLExtractor(Extractor) :
	def __init__(self, ressource, task):
		self.ressource	= ressource
		self.task		= task
	
	def build_doc(self, tmp):
		return html.document_fromstring(str(tmp.read()), base_url=self.task.url)
	
	def extract(self, tmp):
		doc	= self.build_doc( tmp )
		doc.make_links_absolute(self.task.url, resolve_base_href=True)
		collected_urls = [ 
			link for (element, attribute, link, pos) in doc.iterlinks() ]
		
		return buildFromURIs( collected_urls )

class DirectoryExtractor( Extractor ) :
	def __init__(self, ressource, task):
		self.ressource	= ressource
		self.task		= task
		
	def extract(self, nothing=None):
		"""
		nothing pour compatibilitéavec le reste
		"""
		tasks = []
		for child in self.ressource._children :
			tmp_ext	= init_extractor( child, self.task ) 
			if tmp_ext :
				tasks.extend( tmp_ext.extract( child._tmp ) )
			
		return tasks
