from urllib.parse import urlparse
import time

import libtorrent as lt

TASK_WEB_STATIC 	= 0
TASK_WEB_STATIC_TORRENT		= 1
TASK_WEB_STATIC_TOR			= 2

NO_AUTH				= 0
AUTH_FORM			= 1
AUTH_HTTP_BASIC		= 2
AUTH_HTTP_DIGEST	= 3
AUTH_FTP			= 4

MAX_REFRESHRATE		= 20

class TaskFactory:
	def buildFromURI( url, parentTask ):
		task 	= Task(url)
		
		if url[-6:] == ".onion" :
			task.nature	= TASK_WEB_STATIC_TOR
		elif url[:9] == "magnet://" :
			task.nature	= TASK_WEB_STATIC_TORRENT
			task.is_dir = True
		else:
			task.nature	= TASK_WEB_STATIC
		
		task.auth	= parentTask.auth 
		return task
	
	def buildFromURIs(urls, parentTask):
		return [TaskFactory.buildFromURI(url, parentTask) for url in urls ]
	
	def buildFromFile( ressource, tmpFile, parentTask ):
		"""
			@brief Mainly use for .torrent
		"""
		
		if ressource.metadata.contentType == "application/x-bittorrent" :
			tmpFile.rollover()
			task 	= Task( lt.make_magnet_uri( lt.torrent_info( tmpFile.name ) ), nature=TASK_WEB_STATIC_TORRENT, is_dir=True  )
			return task
			
		return None
		
		
class Task:
	def __init__(self, url="", lastvisited=-1, lastcontrolled=-1, lasthash="", refreshrate=1, nature=TASK_WEB_STATIC, auth=NO_AUTH, is_dir=False):
		self.nature	= nature
		self.url	= url
		self.auth	= auth
		
		urlObj		= urlparse( url )
		
		self.scheme		= str(urlObj.scheme)
		self.netloc		= str(urlObj.netloc)
		self.path		= str(urlObj.path)
		self.params		= str(urlObj.params)
		self.query		= str(urlObj.query)
		self.fragment	= str(urlObj.fragment)
		
		self.lastvisited 	= lastvisited
		self.lastcontrolled = lastcontrolled #by a master
		self.lasthash		= lasthash
		self.refreshrate 	= refreshrate #highter => higher delay between to crawl 
		
		self.nature		= nature
		self.auth		= auth
		self.is_dir		= is_dir
		
	def incr(self):
		if self.refreshrate < MAX_REFRESHRATE:
			self.refreshrate+=1
	
	def decr(self):
		if self.refreshrate > 1 :
			self.refreshrate-=1
	
	def is_alive(self, delay):
		return time.time() - self.lastcontrolled <  self.refreshrate * delay
		
	def is_expediable(self, delay):
		return time.time() - self.lastvisited >  self.refreshrate * delay
