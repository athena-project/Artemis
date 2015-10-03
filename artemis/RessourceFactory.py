import hashlib
import os
import tempfile
from .extractors.Extractor import init_extractor
import artemis.pyHermes as pyHermes
import mimetypes

mimetypes.init()


def hashfile_aux(afile, hasher, blocksize=65536):
	buf = afile.read(blocksize)
	while len(buf) > 0:
		hasher.update(buf)
		buf = afile.read(blocksize)
		
def hashfile(afile, hasher, blocksize=65536):
	hashfile_aux(afile, hasher, blocksize)
	return hasher.hexdigest()

#def hashdir(path, hasher, blocksize=65536): for python 3.5
	#buff = ""
	#for entry in os.scandir(path):
		#if entry.is_file():
			#hashfile_aux( os.path.join(path, entry.name) , hasher, blocksize)
		#elif entry.is_dir() and entry.name != "."  and entry.name != "..":
			#hashdir( os.path.join(path, entry.name), hasher, blocksize)
	#return hasher.hexdigest()

#for python<3.5
def hashdir(path, hasher, blocksize=65536): 
	buff = ""
	for path, dirs, files in os.walk(path):
		for filename in files:
			hashfile_aux( open(os.path.join(path, entry.name), "rb") , hasher, blocksize)			
	return hasher.hexdigest()
				
def filesize(afile):
	current = afile.tell()
	afile.seek(0, os.SEEK_END)
	size = afile.tell()
	afile.seek(current, os.SEEK_SET)
	return size
	
def dirsize(path):
	size = 0
	for entry in os.scandir(path):
		if entry.is_file():		
			size += os.path.getsize( os.path.join(path, entry.name) )
		elif entry.is_dir() and entry.name != "."  and entry.name != "..":
			size += dirsize( os.path.join(path, entry.name) )
	return size
    	
class RessourceFactory:
	def build(tmpFile, task, raw_contentType, contentTypes, source): # source for exeample user agent 
		if not tmpFile :
			return None, [], []
		
		if not task.is_dir:	
			h_sha512 = hashfile(tmpFile, hashlib.sha512())
		else :
			h_sha512 = hashdir(tmpFile.name, hashlib.sha512())
		
		raw_contentType			= raw_contentType.split(";")
		if len(raw_contentType)>1 :
			contentType, charset	= raw_contentType[0].strip(), raw_contentType[1].strip()
		else:
			contentType, charset	= raw_contentType[0].strip(), ""

		
		if (contentType in contentTypes and not contentTypes[contentType]) or ( not contentTypes["*"] and contentType not in contentTypes) :
			task.incr()
			return None, [], [] 
		
		if not task.is_dir and h_sha512 == task.lasthash :
			task.incr()
			return None, [], [] 
		
		print("Ressource handling under way")
		task.lasthash = h_sha512
		
		
		ressource	= pyHermes.Ressource(0,0)
		class_type 	= ressource.contentType2ClassType( contentType )
		if class_type == pyHermes.t_Directory :
			ressource = pyHermes.Directory(0)
		elif class_type == pyHermes.t_Document :
			ressource = pyHermes.Document(0)
		elif class_type == pyHermes.t_Text :
			ressource = pyHermes.Text(0)
		elif class_type == pyHermes.t_Video :
			ressource = pyHermes.Video(0)
		elif class_type == pyHermes.t_Image :
			ressource = pyHermes.Image(0)
		elif class_type == pyHermes.t_Audio :
			ressource = pyHermes.Audio(0)
		
		
		metadata	= ressource.getMetadata()	
		metadata.set( "source_type", str(source) )
		metadata.set( "source_location", str(task.url) )
		metadata.set( "source_time", str(task.lastvisited) )
		
		metadata.set("contentType", str(contentType) )
		metadata.set("sha512", str(h_sha512) )
		if not task.is_dir:
			metadata.set("size", str( filesize(tmpFile) ) )
		else:
			metadata.set("size", str(dirsize(tmpFile) ) )
					
		tasks, forms, children	= [], [], {}
		for key in range( NUM_CLASS_TYPES ):
			children[key]=[]
			
		extractor	= init_extractor(contentType, task, tmpFile)
		if extractor :
			tasks, forms = extractor.extract()
		
		#recursive construction for dir, will crash if dept dir >999
		local_path, local_dirs, local_files = os.walk(tmpFile.name , topdown=True).__next__() #only the first layer
		
		for local_dir in local_dirs:
			local_ressource, local_tasks, local_forms, local_children = RessourceFactory.build( 
				{ "name": os.join(local_path+"/", local_dir) }, 
				Task(task.url, nature=task.nature, is_dir=True), #task.url, or task.url+other, nature = un truc inutile ??, source local_recurse ??
				"inode/directory", 
				contentTypes, 
				source)
			
			tasks.extend( local_tasks )
			forms.extend( local_forms )
			ressource.add_child( local_ressource )
			
			children[ local_ressource.getClass_type() ].append( local_ressource )
			for key, r in local_children.items():
				children[ key ].append( r )
		
		for local_file in local_files:
			location = os.join(local_path+"/", local_file) 

			local_ressource, local_tasks, local_forms,local_children = RessourceFactory.build( 
				open(location, "rb"), #1Mo, 
				Task(task.url, nature=task.nature, is_dir=False), #task.url, or task.url+other, nature = un truc inutile ??, source local_recurse ??
				mimetypes.guess_type(location, strict=False)[0], 
				contentTypes, 
				source)
			
			tasks.extend( local_tasks )
			forms.extend( local_forms )
			ressource.add_child( local_ressource )
			
			children[ local_ressource.getClass_type() ].append( local_ressource )
			for key, r in local_children.items():
				children[ key ].append( r )
		
		return ressource, tasks, forms, children

		
