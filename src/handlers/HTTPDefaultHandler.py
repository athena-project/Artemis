import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import tempfile
from email.utils import formatdate
from artemis.Task import Task, AuthNature, TaskNature
import logging

import pycurl #until requests support sock5, no accreditation handling, http://tech.michaelaltfield.net/2015/02/22/pycurl-through-tor-without-leaking-dns-lookups/


class HTTPDefaultHandler:
	def __init__(self, useragent, contentTypesHeader, accreditationCache, 
	proxies=None, tor_socket_port=7000):
		self.contentTypesHeader			= contentTypesHeader
		self.accreditationCache 		= accreditationCache
		self.useragent					= useragent
		self.tor_socket_port			= tor_socket_port
		
		self.s							= requests.Session()
		self.newTasks					= [] #redirection ones
		if proxies : 
			self.s.proxies	= proxies
				
	def buildHeaders(self, task):
		headers = {"User-Agent":self.useragent,
					"Accept":self.contentTypesHeader}
		if task.lastvisited != -1:
			headers["If-Modified-Since"]= formatdate( 
				timeval = task.lastvisited, 
				localtime = False, 
				usegmt = True)
		return headers
		
	def checkHeaders(self,task, status_code, headers):
		if task.lastvisited != -1:
			if( (status_code == 301 or status_code ==302 
				or status_code ==307 or status_code ==308) 
			and "Location" in headers): #redirection
				task.incr()
				self.newTasks.append( Task(headers["Location"] ) )
				return False
			elif status_code == 304 : #Content unchange
				task.incr()
				return False
			elif status_code > 400 : #ie 4xx or 5xx error
				task.incr()
				logging.debug( status_code, task.url )
				return False
		return True
		
	def checkHeader(self, task):
		r = self.s.head(task.url, headers=self.buildHeaders(task) )
		return self.checkHeaders(task, r.status_code, r.headers)
		
	def header_function_pycurl(self, header_line):
		header_line = header_line.decode('iso-8859-1')
		if ':' not in header_line:
			return

		name, value = header_line.split(':', 1)
		name = name.strip().lower()
		value = value.strip()

		self.tor_headers[name] = value
	
	def tor_pycurl(self, task):
		self.tor_headers = {} #response headers
		tmpFile	= tempfile.SpooledTemporaryFile(max_size=1048576) #1Mo
		
		query = pycurl.Curl()
		query.setopt(pycurl.URL, task.url)
		query.setopt(pycurl.PROXY, '127.0.0.1')
		query.setopt(pycurl.PROXYPORT, self.tor_socket_port)
		query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
		query.setopt(pycurl.HTTPHEADER, [ 
			''.join( [str(k), ":", str(v)]) 
			for k,v in self.buildHeaders(task).items()] )
		query.setopt(pycurl.WRITEFUNCTION, tmpFile.write)
		query.setopt(pycurl.HEADERFUNCTION, self.header_function_pycurl)
		query.perform()
		
		
		status_code = query.getinfo(pycurl.HTTP_CODE)
		query.close()
		headers=self.tor_headers

		if self.checkHeaders(task, status_code, headers) :
			return headers["content-type"], tmpFile, self.newTasks
		return None, None, self.newTasks

	def getAccreditation(self, task):
		if task.auth == AuthNature.no :
			return None
		elif task.auth == AuthNature.form :
			self.s.cookies	= self.accreditationCache.get(task.auth, task)
			return None
		elif task.auth == AuthNature.http_basic : 
			user = self.accreditationCache.get(task.auth, task )
			return HTTPBasicAuth(user.login, user.password)
		elif task.auth == AuthNature.htto_digest :
			user = self.accreditationCache.get(task.auth, task )
			return HTTPDigestAuth(user.login, user.password)
		
	def execute(self, task):
		if task.nature == TaskNature.web_static_tor:
			return self.tor_pycurl( task)
		
		with self.s :
			if self.checkHeader(task):
				headers = {"User-Agent":self.useragent,
							"Accept":self.contentTypesHeader}
				r = self.s.get(task.url, headers=headers, 
					auth=self.getAccreditation(task), stream=True )

				if r.status_code != 200 : #ie 4xx or 5xx error
					task.incr()
					logging.debug( ' '.join( [ 
						task.url, str(r.status_code) ]) )
					return None, None, []
				
				tmpFile	= tempfile.SpooledTemporaryFile(max_size=1048576) #1Mo
				for block in r.iter_content(4096):
					tmpFile.write(block)
				
				return r.headers["Content-Type"], tmpFile, self.newTasks
		return None, None, self.newTasks
	
		
