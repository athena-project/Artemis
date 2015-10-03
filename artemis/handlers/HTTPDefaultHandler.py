import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import tempfile
from email.utils import formatdate
from artemis.Task import Task, TASK_WEB_STATIC_TOR, NO_AUTH, AUTH_FORM, AUTH_HTTP_BASIC, AUTH_HTTP_DIGEST
import logging

import pycurl #until requests support sock5, no accreditation handling, http://tech.michaelaltfield.net/2015/02/22/pycurl-through-tor-without-leaking-dns-lookups/


class HTTPDefaultHandler:
	def __init__(self, useragent, contentTypesHeader, accreditationCacheHandler, proxies=None, tor_socket_port=7000):
		self.contentTypesHeader			= contentTypesHeader
		self.accreditationCacheHandler 	= accreditationCacheHandler
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
			#print(formatdate( timeval = task.lastvisited, localtime = False, usegmt = True))
			headers["If-Modified-Since"]= formatdate( timeval = task.lastvisited, localtime = False, usegmt = True)
		return headers
		
	def checkHeaders(self,task, status_code, headers):
		if task.lastvisited != -1:
			if (status_code == 301 or status_code ==302 or status_code ==307 or status_code ==308) and "Location" in headers: #redirection
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
		#print(r.status_code)
		return self.checkHeaders(task, r.status_code, r.headers)
		
	def header_function_pycurl(self, header_line):
		# HTTP standardpycurl specifies that headers are encoded in iso-8859-1.
		header_line = header_line.decode('iso-8859-1')

		# Header lines include the first status line (HTTP/1.x ...).
		# We are going to ignore all lines that don't have a colon in them.
		# This will botch headers that are split on multiple lines...
		if ':' not in header_line:
			return

		# Break the header line into header name and value.
		name, value = header_line.split(':', 1)

		# Remove whitespace that may be present.
		# Header lines include the trailing newline, and there may be whitespace
		# around the colon.
		name = name.strip()
		value = value.strip()

		# Header names are case insensitive.
		# Lowercase name here.
		name = name.lower()

		# Now we can actually record the header name and value.
		self.tor_headers[name] = value
	
	
	def tor_pycurl(self, task):
		self.tor_headers = {} #response headers
		tmpFile	= tempfile.SpooledTemporaryFile(max_size=1048576) #1Mo
		
			
		
		query = pycurl.Curl()
		query.setopt(pycurl.URL, task.url)
		query.setopt(pycurl.PROXY, '127.0.0.1')
		query.setopt(pycurl.PROXYPORT, self.tor_socket_port)
		query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
		query.setopt(pycurl.HTTPHEADER, [ str(k)+":"+str(v) for k,v in self.buildHeaders(task).items()] )
		query.setopt(pycurl.WRITEFUNCTION, tmpFile.write)
		query.setopt(pycurl.HEADERFUNCTION, self.header_function_pycurl)
		query.perform()
		
		
		status_code = query.getinfo(pycurl.HTTP_CODE)
		query.close()
		headers=self.tor_headers
		#print(headers)
		if self.checkHeaders(task, status_code, headers) :
			return headers["content-type"], tmpFile, self.newTasks
		return None, None, self.newTasks

	def getAccreditation(self, task):
		if task.auth == NO_AUTH :
			return None
		elif task.auth == AUTH_FORM :
			self.s.cookies	= self.accreditationCacheHandler.get(task.auth, task )
			return None
		elif task.auth == AUTH_HTTP_BASIC : 
			user = self.accreditationCacheHandler.get(task.auth, task )
			return HTTPBasicAuth(user.login, user.password)
		elif task.auth == AUTH_HTTP_DIGEST :
			user = self.accreditationCacheHandler.get(task.auth, task )
			return HTTPDigestAuth(user.login, user.password)
		
	def execute(self, task):
		if task.nature == TASK_WEB_STATIC_TOR:
			return self.tor_pycurl( task)
			
		if self.checkHeader(task):
			headers = {"User-Agent":self.useragent,
						"Accept":self.contentTypesHeader}
			r = self.s.get(task.url, headers=headers, auth=self.getAccreditation(task), stream=True )
			#print(r)
			if r.status_code != 200 : #ie 4xx or 5xx error
				task.incr()
				logging.debug( r.status_code, task.url, r.content() )
				return None, None
			
			tmpFile	= tempfile.SpooledTemporaryFile(max_size=1048576) #1Mo
			for block in r.iter_content(4096):
				tmpFile.write(block)
				
			return r.headers["Content-Type"], tmpFile, self.newTasks
		return None, None, self.newTasks
	
		
