from lxml import html
from .Form import build
from artemis.handlers.HandlerRules import getHandler
from artemis.Task import buildFromURI, Task, AuthNature

import formasaurus
 
class FormHandler :
	def __init__(self):
		pass

	def extract(self, url, nature ):
		task = TaskFactory.buildFromURI( url, Task(auth=AuthNature.no ))
		handler =  getHandler(task)("*", "*/*;", None) #pas de cache
		contentTypes, tmpFile, newTasks = handler.execute( task )
		
		doc = html.document_fromstring(str(tmpFile.read()), base_url=task.url)
		
		forms= []
		for form, cl in formasaurus.extract_forms(doc):
			if nature == cl :
				forms.append( build( url, html.tostring(form), nature ) )

		return forms
		
	def extractOne(self, url, nature ):
		task = TaskFactory.buildFromURI( url, Task(auth=AuthNature.no ))
		handler =  getHandler(task)("*", "*/*", None)
		contentType, tmpFile, redirectionTasks = handler.execute( task )
		
		if not tmpFile:
			return None
			
		tmpFile.seek(0)
		doc = html.document_fromstring(str(tmpFile.read()), base_url=task.url)

		ex = FormExtractor.load()
		for form, cl in ex.extract_forms(doc):
			if nature.value == cl:
				return build( url, form, nature)
