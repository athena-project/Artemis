from time import time
from urllib.robotparser import RobotFileParser as urllib_RobotFileParser
import urllib.request
import logging
from .Cache import ARCCache
from .Cache import ARCCache, EmptyItem
from .Task import Task, TaskNature
import traceback, sys

class UpdateError(Exception):
	pass

class RobotFileParser( urllib_RobotFileParser ) :
	""" 
		@brief extract sitemap too
	"""
	def __init__(self, url=''):
		self.entries = []
		self.default_entry = None
		self.disallow_all = False
		self.allow_all = False
		self.set_url(url)
		self.last_checked = 0

		self.sitemaps = []

	def parse(self, lines):
		"""Parse the input lines from a robots.txt file.

		We allow that a user-agent: line is not preceded by
		one or more blank lines.
		"""
		# states:
		#   0: start state
		#   1: saw user-agent line
		#   2: saw an allow or disallow line
		state = 0
		entry = urllib.robotparser.Entry()
		
		self.modified()
		for line in lines:
			if not line:
				if state == 1:
					entry = urllib.robotparser.Entry()
					state = 0
				elif state == 2:
					self._add_entry(entry)
					entry = urllib.robotparser.Entry()
					state = 0
			# remove optional comment and strip line
			i = line.find('#')
			if i >= 0:
				line = line[:i]
			line = line.strip()
			if not line:
				continue

			line = line.split(':', 1)
			if len(line) == 2:
				line[0] = line[0].strip().lower()
				line[1] = urllib.parse.unquote(line[1].strip())
				if line[0] == "user-agent":
					if state == 2:
						self._add_entry(entry)
						entry = urllib.robotparser.Entry()
					entry.useragents.append(line[1])
					state = 1
				elif line[0] == "disallow":
					if state != 0:
						entry.rulelines.append( 
							urllib.robotparser.RuleLine(line[1], False))
						state = 2
				elif line[0] == "allow":
					if state != 0:
						entry.rulelines.append( 
							urllib.robotparser.RuleLine(line[1], True))
						state = 2
				elif line[0] == "sitemap":
					self.sitemaps.append( line[1] )
		if state == 2:
			self._add_entry(entry)

class Robot:
	def __init__(self, url, deathtime, useragent):
		self.url		= url
		self.deathtime  = deathtime
		self.useragent	= useragent
		
		self._robotparser	= RobotFileParser(url)

	def update(self, lifetime):
		self.deathtime	= time() + lifetime
		try:
			self._robotparser.read()
			self._robotparser.modified()
		except Exception as e :
			logging.debug( "%s %s %s" % (
				traceback.extract_tb(sys.exc_info()[2]), str(e), self.url))
			
	def is_alive(self):
		return time()<self.deathtime
	
	def can_fetch(self, url):
		return self._robotparser.can_fetch(self.useragent, url)
		
class RobotCache(ARCCache):
	def __init__(self, size, useragent="*", lifetime=3600):
		"""
			@param liftime		- lifetime( second ) of a robot object before updating
			
		"""
		ARCCache.__init__(self, size)
		
		self.lifetime 		= lifetime
		self.useragent		= useragent
	
	def get(self, task):
		if( task.scheme.lower() not in ["http", "https"] 
		or task.nature == TaskNature.web_static_tor):
			return True, []
			
		robot_url = ''.join( 
			[task.scheme, "://", task.netloc, "/robots.txt"])
		
		robot =	self[robot_url]
		sitemaps = []
		
		if isinstance( robot, EmptyItem):
			robot = Robot( robot_url, 0, self.useragent )
			self[robot_url] = robot
			
		if not robot.is_alive() :
			robot.update(self.lifetime)
			if robot._robotparser.sitemaps :
				sitemaps =[
					Task( tmp_url,  nature=TaskNature.web_static_sitemap)
					for tmp_url in robot._robotparser.sitemaps ]
		return robot.can_fetch(task.url), sitemaps
