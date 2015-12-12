#import unittest
##from artemis.tests.CacheTest import TestARCCache, TestDeque, TestHybridCache
##from artemis.tests.RobotTest import TestRobotCache
##from artemis.tests.AccreditationTest import AccreditationTest
##from artemis.tests.ExtractorTest import ExtractorTest
#from artemis.tests.AVLTest import AVLTest

#unittest.main()
from threading import Thread, RLock, Event

lock = RLock()

class T1(Thread):
	def __init__(self, d):
		self.d =d 
		Thread.__init__(self)

	def run(self):
		for i in range(1000000):
			with lock:
				print("b")

				self.d[i] = 0
	

class T2:
	def __init__(self):		
		self.d = {}
		self.t = T1( self.d )
	
	def run(self):
		with lock:
			self.t.start()
		while True:
			print("a")	
			for k in self.d.values():
				pass
	
t = T2()
t.run()
