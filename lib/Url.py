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
#	@author Severus21
#
from urllib.parse import urlparse

import SQLFactory
import RedisFactory
import hashlib
from collections import deque

	
class RedisManager:
	def __init__(self):
		"""
			@brief provide an interface between redis and url-object
		"""
		self.con = RedisFactory.getConn()
		
	def get( self, url):
		m_sha1 = hashlib.sha1()
		m_sha1.update( url.encode() )
		h_sha1 = m_sha1.hexdigest()
		
		tmp = self.con.get(  'urlrecord_'+h_sha1 )
		
		if tmp != None :
			return float( tmp )
		else :
			return 0
	
	def add( self, url, time):
		m_sha1 = hashlib.sha1()
		m_sha1.update( url.encode() )
		h_sha1 = m_sha1.hexdigest()
		
		self.con.set(  'urlrecord_'+h_sha1 , time)
		
class Url:
	def __init__(self,url, o="", t="", charset="", alt=""):
		"""
			@param o		- describes the parent balise of the current url
			@param t		- content type if provided(optionally with charset)
			@param charset	- 
			@param alt		- description of the link if provided
		"""
		self.origin 	= o
		self.url		= url
		
		t = t.split(";")
		self.type 		= t[0].strip() # contentType without charset
		if len(t)>1 and (not charset):
			charset = t[1].split("=")
			if len(charset)>1:
				charset	= charset[1]
			else:
				charset = charset[0]
				
		self.charset 	= charset.strip()
		self.alt 		= alt
		
		
	def size(self):
		return len(self.origin)+len(self.url)+len(self.type)+len(self.charset)+len(self.alt)
	
	def serializeSize(self):
		return self.size()+4
		
	def serialize(self):
		return self.origin+"|"+self.url+"|"+self.type+"|"+self.charset+"|"+self.alt

#Static function

def serializeList(l):
	buff = ""
	for url in l:
		buff+=url.serialize()+"~"
	return buff
		
def unserialize(s):
	origin, url, type, charset, alt= "", "", "", "", ""
	i,k=0,0

	for j in range(0, len(s)):
		if s[j] == "|":
			if k==0:
				origin	= s[i:j]
			if k==1:
				url		= s[i:j]
			if k==2:
				type	= s[i:j]
			if k==3:
				charset	= s[i:j]
			if k==4:
				alt	=s[i:j]
				
			i,k=j+1,k+1
			
	return Url( url, origin, type, charset, alt)

def unserializeList(s):
	l = []
	i=0
	for j in range(0, len(s)):
		if s[j] == "~":
			l.append( unserialize( s[i:j] ) )
			i=j+1
			
	return l


def makeBundle(urls, maxlen):
	"""
		@param urls				- a deque of urls
		@param maxlen			- the bundle is bounded to the specified maximum length
		@brief Prepare a bundle of urls to sending 
	"""
	bundle = ""
	 
	try:
		for i in range(0, maxlen):
			url 	= urls.popleft()
			url		= url.serialize()+"~" 
			bundle	+=url
	except Exception:
		pass
		
	return bundle

def makeCacheBundle(cacheHandler, fValid, redis, delay, maxlen):
	"""
		@param cacheHandler		- see UrlCacheHandler.py
		@param redis			- a redis handler
		@param delay 			- delay between two update for an url
		@param maxSize			- the bundle is bounded to the specified maximum length
		@brief Prepare a bundle of urls to sending, from urlCacheHandler
	"""
	bundle = ""
	i = 0
	
	while i<maxlen and not cacheHandler.empty():
		url = cacheHandler.get()
		if not fValid( url, cacheHandler, redis, delay):
			pass
		else :	
			i		+= 1
			url		= url.serialize()+"~" 
			bundle	+=url
	
	return bundle
