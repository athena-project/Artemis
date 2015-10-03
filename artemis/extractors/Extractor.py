from .HtmlExtractor import HTMLExtractor

class Extractor :
	def __init__(task, tmpFile):
		self.task		= task
		self.tmpFile	= tmpFile
	
	def extract(self):
		return [], []	

def init_extractor(contentType, task, tmpFile):
	if contentType == "text/html" : 
		return HTMLExtractor(task, tmpFile)
	else:
		pass 
