import hashlib
import os
import tempfile
from .extractors.ExtractorFactory import init_extractor
from hermes.RessourceFactory import DEFAULT_CONTENT_TYPE, build as build_ressource

	#"""
		#tmp	: temporaryDirector, str => directory
					#temporaryFile,file => file
		#contentTypes : rules to build or not ressource
	#"""
def build(tmp, task, raw_contentType, contentTypes, source): # source default it's uri
		if not tmp:
			return None, []
		
		#Checking content-type
		if raw_contentType:
			contentType	= (raw_contentType.split(";"))[0].strip()
		else:
			contentType = DEFAULT_CONTENT_TYPE
			
		if not contentTypes[contentType] :
			task.incr()
			return None, []
		
		ressource = build_ressource( tmp, raw_contentType)
		ressource.generate_id_rec( task.url )
		
		if ressource._metadata["sha224"] == task.lasthash :
			task.incr()
			return ressource, []
		
		task.lasthash = ressource._metadata["sha224"]
		
		ressource._metadata["source"] = source
		
		tasks	= []
		extractor	= init_extractor(ressource, task)
		if extractor :
			tasks = extractor.extract(tmp)
				
		return ressource, tasks
