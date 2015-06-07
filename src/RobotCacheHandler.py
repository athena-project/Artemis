import time
import urllib.robotparser
import logging
from .LimitedCollections import LimitedDict

class RobotFileParser( urllib.robotparser.RobotFileParser) :
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
		
		self.sitemap=""

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
		entry = Entry()

		for line in lines:
			if not line:
				if state == 1:
					entry = Entry()
					state = 0
				elif state == 2:
					self._add_entry(entry)
					entry = Entry()
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
						entry = Entry()
					entry.useragents.append(line[1])
					state = 1
				elif line[0] == "disallow":
					if state != 0:
						entry.rulelines.append(RuleLine(line[1], False))
						state = 2
				elif line[0] == "allow":
					if state != 0:
						entry.rulelines.append(RuleLine(line[1], True))
						state = 2
				elif line[0] == "sitemap":
					self.sitemap = line[1]
		if state == 2:
			self._add_entry(entry)

class Robot:
	def __init__(self, robotparser, url, deathtime):
		self.robotparser = robotparser
		self.deathtime = deathtime
		self.robotparser.set_url( key )
		
		
	def update(self):
		try:
			self.robotparser.read()
			self.robotparser.modified()
		except Exception as e :
			logging.info("RobotCacheHandler  ", e)
			
	def is_alive(self):
		return time.time()<self.deathtime

class RobotCacheHandler(LimitedDict):
	def __init__(self, mem_max, initialdata=None, lifetime=3600):
		"""
			@brief				blocking, blocking and vblocing io mustbe changed
			@param liftime		- lifetime( second ) of a robot object before updating
			
		"""
		LimitedDict.__init__(self, mem_max, initialdata)
		self.lifetime 		= lifetime

	
	def add(self, key):
		"""
			@return sitemap url
		"""
		if (key in self) and self[key].is_alive() :
			return ""
				
		robot = Robot( RobotFileParser(), key, time.time() + self.lifetime )
		LimitedDict.__setitem__(self, key, robot )
		return 
		

	def __getitem__( self, key ):
		if (key in self) and self[key].is_alive() :
			return LimitedDict.__getitem__(self, key)
		else:
			robot = LimitedDict.__getitem__(self, key)
			robot.update()
			return robot
