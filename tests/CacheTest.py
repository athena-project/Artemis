import unittest
from .Benchmark import Timer 
from artemis.Cache import *

class TestDeque(unittest.TestCase):
	def test_valid(self):
		n	= 10000
		d	= Deque()
		
		for k in range(1, n+1):
			d.appendleft( k )
			
		for k in range(1, n+1):
			self.assertTrue( d.__contains__(k) )
			self.assertFalse( d.__contains__(3*(k+n)) )
			
		for k in range(1, n):
			self.assertEqual( d.pop(), k)
			
	def test_time_O1(self):
		n	 	 = 1000
		counters = [ [], [], [], [] ]
		d	= Deque()
		
		
		
		for i in range( 11 ):
			with Timer() as timer:
				for k in range( n*(2**i) ):
					d.appendleft( k )
					
			counters[0].append( timer.interval )
			
			with Timer() as timer:
				for k in range( n*(2**i) ):
					d.__contains__( k )
					
			counters[1].append( timer.interval )
			
			with Timer() as timer:
				for k in range( n*(2**i) ):
					d.pop()
					
			counters[2].append( timer.interval )
			
			with Timer() as timer:
				for k in range( n*(2**i) ):
					d.__contains__( k )
					
			counters[3].append( timer.interval )
	
		for i in range(4):
			for j in range(9):
				self.assertTrue( counters[i][j+1]<3*counters[i][j])
	
	def test_space_O1(self):
		n	= 10000
		d	= Deque()
		
		for k in range(1, n+1):
			d.appendleft( k )
			self.assertEqual( len(d), k)
		
		for k in range(1, n):
			self.assertEqual( d.pop(), k)
			self.assertEqual( len(d), n-k)
		
class TestARCCache(unittest.TestCase):
	def test_valid(self):
		n	= 1000
		c	= ARCCache(n+1)
		
		for k in range(n):
			c[k]=k
			self.assertEqual( c[k], k)
			self.assertEqual( len(c),  k+1)
		
		for k in range(n):
			self.assertEqual( c[k], k)
			c[k] = k+10
			
		for k in range(n):
			self.assertEqual( c[k], k+10)
		
		#test LRU comportement
		c[n]	= n+10
		self.assertTrue( isinstance( c[0], EmptyItem) )
		self.assertEqual( c[n], n+10 )
		
		#test LFU comportement
		for i in range(15): # on augmente la frequence
			for k in range(int(n/2), n):
				c[k]
		for i in range(2*n, 2*n+int(n/2)-1):
			c[i] = i
			
		for k in range(int(n/2), n):
			self.assertEqual( c[k], k+10)

	def test_time_O1(self):
		n=1000
		counters = [ [], [] ]
		
		for i in range( 11 ):
			c	= ARCCache( n*(2**i) )
			with Timer() as timer :
				for k in range( n*(2**i) ):
					c[k] = k
			counters[1] .append( timer.interval )
			
			with Timer() as timer :
				for k in range( n*(2**i) ):
					c[k]
			counters[0] .append( timer.interval )
		
		for i in range(2):
			for j in range(9):
				self.assertTrue( counters[i][j+1]<3*counters[i][j])
				
	def test_space_O1(self):
		n	= 10000
		c	= ARCCache(n)
		
		for k in range(n):
			c[k]=k
			self.assertEqual( len(c), k+1)
			self.assertTrue( len(c.t1) + len(c.b1) + len(c.t2) + len(c.b2) < 2*(k+1) )

class TestHybridCache(unittest.TestCase):
	def test_valid(self):
		n 	= 10000
		d	= HybridCache(2*n, n) 

		for k in range(2*n):
			d[str(k)]= k
			self.assertEqual( d[str(k)], k)
		
		for k in range(2*n):
			self.assertEqual( d[str(k)], k)
				
		#Out of limits
		for k in range(3*n):
			d[str(k)]= k
		
		for k in range(2*n):
			self.assertEqual( d[str(k)], k)
			
		for k in range(2*n, 3*n):
			with self.assertRaises(KeyError):
				d[str(k)]
		
	def test_time_O1_cached(self):
		n=1000
		counters = [ [], [] ]
		
		for i in range( 10 ):
			d	= HybridCache( 2*n*(2**i), n*(2**i) )
			with Timer() as timer :
				for k in range( n*(2**i) ):
					d[str(k)] = k
			counters[0] .append( timer.interval )
			
			with Timer() as timer :
				for k in range( n*(2**i) ):
					d[str(k)]
			counters[1] .append( timer.interval )
					
		for i in range(2):
			for j in range(9):
				self.assertTrue( counters[i][j+1]<3*counters[i][j])
