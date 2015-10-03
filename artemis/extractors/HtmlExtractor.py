from lxml import html
from artemis.Task import TaskFactory
from artemis.Forms import FormFactory
from urllib.parse import urlparse

from formasaurus import FormExtractor
 
class HTMLExtractor :
	def __init__(self, task, tmpFile):
		self.task		= task
		self.tmpFile	= tmpFile
	
	def extract(self):
		self.tmpFile.seek(0)
		doc = html.document_fromstring(str(self.tmpFile.read()), base_url=self.task.url)
		urls = doc.xpath('//a/@href')
		urls.extend( doc.xpath('//img/@src') )
		urls.extend( doc.xpath('//link/@href') )
		urls.extend( doc.xpath('//script/@src') )
		urls.extend( doc.xpath('//source/@src') )
		
		new_urls = []
		for url in urls:
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
				
			new_urls.append( url )
		
		forms		= []
		ex = FormExtractor.load()
		#print("begin form parsing")
		for form,cls in ex.extract_forms(doc):
			#print("cls: ", cls)
			forms.append( (html.tostring(form), cls) )

		return TaskFactory.buildFromURIs( new_urls, self.task ), FormFactory.build( forms, self.task)		
