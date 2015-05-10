import sys
import collections

class Item:
	def __init__(self, priority, key):
		"""	
			@param	priority	-
			@param	robot 		-
			@brief Object use to represent robot in heapq( priority queue)
		"""
		self.priority	= priority
		self.key 		= key
		
	def __eq__(self,y):
		return self.priority == y.priority
		
	def __ge__(self, y): #x.__ge__(y) <==> x>=y
		return self.priority>=y.priority
		
	def __gt__(self, y): # x.__gt__(y) <==> x>y
		return self.priority>y.priority
	
	def  __le__(self, y): # x.__le__(y) <==> x<=y
		return self.priority<=y.priority
		
	def  __lt__(self, y): # x.__lt__(y) <==> x<y
		return self.priority<y.priority
		
	def incr(self):
		self.priority-=1 #because of sort 
		
	def __repr__(self):
		return str( self.priority) +"_"+str( self.key)


class LimitedDict( collections.UserDict ): #limited in memory
	def __init__(self, mem_max, initialdata=None):
		collections.UserDict.__init__(self, initialdata)
		self.mem_length = 0
		self.mem_max = mem_max
		
		self.accessmap		= [] # heapq
		
		self.suppr_fact   	= 100
		
	def __delitem__(self, key): 
		self.mem_length -= sys.getsizeof( self.data[key] )
		collections.UserDict.__delitem__(self, key)
		
	def prune(self, length):
		length = min( self.mem_max-1, self.suppr_fact * length )
		while  self.mem_length + length < self.mem_max :
			self.accessmap.sort()
			it = self.accessmap.pop()
			self.__delitem__( it.key )
			del it
	
	def __setitem__(self, key, item):
		if self.mem_length + sys.getsizeof( item ) > self.mem_max :
			self.prune( sys.getsizeof( item ) ) 
			
		self.mem_length += sys.getsizeof( item )
		
		it = Item( 0, key)
		if not key in self.data:
			self.accessmap.append( it )
			
		collections.UserDict.__setitem__(self, key, (it,item))
	
	def __getitem__(self, key):
		it, item = collections.UserDict.__getitem__(self, key)
		it.incr()
		return item
		
	
class LimitedDeque:
	def __init__(self, mem_max):
		""" insertion not allowed if mem_max reached"""
		self.mem_length = 0
		self.mem_max = mem_max
		
		self.suppr_fact   	= 100
		self.data 			= collections.deque()
	
	def __len__(self):
		return len( self.data )

	def append(self, item ):
		if self.mem_length + sys.getsizeof( item ) > self.mem_max :
			return False
			
		self.mem_length += sys.getsizeof( item )
		self.data.append( item )
		return True
	
	def appendleft(self, item):
		if self.mem_length + sys.getsizeof( item ) > self.mem_max :
			return False
			
		self.mem_length += sys.getsizeof( item )
		self.data.appendleft( item )
		return True
		
	def pop(self):
		tmp = self.data.pop()
		self.mem_length -= sys.getsizeof( tmp )
		return tmp
		
	def popleft(self):
		tmp = self.data.popleft()
		self.mem_length -= sys.getsizeof( tmp )
		return tmp
	
	
	
	
import unittest
class TestNet(unittest.TestCase):
	def test_limited_dict(self):
		d = LimitedDict(1<<25)
		for i in range(100000):
			d[str(i)]=10000000000000000000000000000 #+40bytes
		print( d["1"] ) 
		d["1"]
		for i in range(100000):
			d[str(i)]=10000000000000000000000000000 #+40bytes
		self.assertTrue( d["1"] == 10000000000000000000000000000 )
	
	def test_limited_deque(self):
		d = LimitedDeque(1<<30)
		for i in range(10000000):
			d.append( """aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
			aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
						"""  ) 
		
		try :
			for i in range(1000000):
				d.pop(  )
		except Exception as e:
			pass
		
		for i in range(1000000):
			d.appendleft( "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"  )
		
		try :	
			for i in range(1000000):
				d.popleft(  )
		except Exception as e:
			pass
		
		
if __name__ == '__main__':
    unittest.main()
