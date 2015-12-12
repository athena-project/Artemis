from urllib.parse import urlparse
import time
from enum import IntEnum
import libtorrent as lt

from collections import defaultdict


MAX_REFRESHRATE		= 20
AVERAGE_TASK_SIZE	= 2048 #à affiner au cours du temps

accreditationRules = defaultdict( lambda : AuthNature.no, {

})

class TaskNature(IntEnum):
	web_static			= 0
	web_static_torrent 	= 1
	web_static_tor		= 2
	web_static_sitemap	= 3
	
class AuthNature(IntEnum):
	no				= 0
	form			= 1
	http_basic		= 2
	http_digest		= 3
	ftp				= 4

#Task Factory
def buildFromURI( url, is_dir=False ):
	task 	= Task(url, is_dir=is_dir)
	
	if task.netloc[-6:] == ".onion" :
		task.nature	= TaskNature.web_static_tor
	elif url[:7] == "magnet:" :
		task.nature	= TaskNature.web_static_torrent
		task.is_dir = True
	else:
		task.nature	= TaskNature.web_static
	
	task.auth	= accreditationRules[ task.netloc ]
	return task

def buildFromURIs(urls, is_dir=False):
	return [buildFromURI(url, is_dir) for url in urls ]

def buildFromFile( ressource, tmpFile ):
	"""
		@brief Mainly use for .torrent
	"""
	
	if ressource.metadata.contentType == "application/x-bittorrent" :
		tmpFile.rollover()
		task 	= Task( 
			lt.make_magnet_uri( lt.torrent_info( tmpFile.name ) ), 
			nature=TaskNature.web_static_torrent, is_dir=True  )
		return task
		
	return None
			
class Task:
	def __init__(self, url="", lastvisited=-1, lastcontrolled=-1, lasthash="", 
	refreshrate=1, nature=TaskNature.web_static, auth=AuthNature.no, is_dir=False):
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
	
	def __str__(self):
		return '|'.join( [self.url, str(self.nature), str(self.auth), str(self.is_dir)] )
