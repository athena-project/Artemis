import unittest
from .Benchmark import Timer 
from artemis.Robot import *
from artemis.Task import Task
from time import sleep

class TestRobotCache(unittest.TestCase):	
	def test_robotparser( self ):
		urls = [
			("https://stackoverflow.com", False),
			("https://www.ovh.com/fr/", True),
			("https://en.wikipedia.org/wiki/SHA-2", True),
			("", True),
			("""magnet:?xt=urn:btih:859da4d7affd6efd937236edf
			b19c5ff1cb51f0a&dn=ubuntu-12.04.5-server-amd64.iso""", 
			True),
			#("http://xmh57jrzrnw6insl.onion", True),
			("ftp://debian.org", True)
		]
		sitemap_urls= [
			[],
			["https://www.ovh.com/sitemap.xml"],
			[],
			[],
			#[],
			[]
		]
		
		c	= RobotCache(1024, "artemis")
		
		for (k, (url, u_flag) ) in enumerate(urls) :
			flag, sitemaps = c.get( Task(url) )
			self.assertEqual( flag, u_flag)
			
			for sitemap in sitemaps:
				self.assertTrue( sitemap.url in sitemap_urls[k])
		
	def test_robotcache(self):
		c	= RobotCache(10, "artemis", 10)
		urls = [
			"https://stackoverflow.com",
			"http://www.mathemainzel.info/files/x86asmref.html",
			"https://en.wikipedia.org/wiki/SHA-2",			
		]
		
		for url in urls :
			flag, sitemaps = c.get( Task(url) )
			
		with Timer() as timer: #use cached
			for urls in urls :
				flag, sitemaps = c.get( Task(url) )
		self.assertTrue( timer.interval < 0.001 )
		
		sleep(10)
		
		with Timer() as timer: #update
			for urls in urls :
				flag, sitemaps = c.get( Task(url) )
		self.assertTrue( timer.interval > 0.01 )
		
