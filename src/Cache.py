import sys
import collections
import shelve 
import tempfile, time
import os


#no thread-safe even for reading 
#LimitedDeque devient deque( size ) on utilisera un calcul en moyenne de charge pour trouver la taille atomic d'un elmts

class Deque:
	"""
		Fast searchable deque, works with uniq items
	"""
	def __init__(self):
		self.od = collections.OrderedDict()
		
	def appendleft(self, k):
		#O(1)
		od = self.od
		if k in od:
			del od[k]
		od[k] = None
	def pop(self):
		#O(1)
		return self.od.popitem(0)[0]
	def remove(self, k):
		#O(1)
		del self.od[k]
	def __len__(self):
		#O(1)
		return len(self.od)
	def __contains__(self, k):
		#O(1)
		return k in self.od
	def __iter__(self):
		#O(1)
		return reversed(self.od)
	def __repr__(self):
		#O(1)
		return 'Deque(%r)' % (list(self),)

class EmptyItem(object):
	def __init__(self):
		pass

class Cache:
	def __init__(self, size):
		self.size	=	size
		
	def items(self):
		pass	
		
class ARCCache(Cache):
	#https://dl.dropboxusercontent.com/u/91714474/Papers/ARC.pdf
	#len(cached)<size
	def __init__(self, size):
		Cache.__init__(self, size)
		self.cached = {}
		self.p = 0
		self.t1 = Deque()
		self.t2 = Deque()
		self.b1 = Deque()
		self.b2 = Deque()

	def replace(self, key):
		if len(self.t1)>0 and (
		(key in self.b2 and len(self.t1) == self.p) or
		(len(self.t1) > self.p)):
			old = self.t1.pop()
			self.b1.appendleft(old)
		else:
			old = self.t2.pop()
			self.b2.appendleft(old)
		
		del(self.cached[old])
        
	def __getitem__(self, key):
		if not key in self.cached:
			return EmptyItem()
		
		if key in self.t1: 
			self.t1.remove(key)
		elif key in self.t2: 
			self.t2.remove(key)
			
		self.t2.appendleft(key)
		return self.cached[key]

	def __setitem__(self, key, item): 
		if key in self.cached:
			if key in self.t1: 
				self.t1.remove(key)
			elif key in self.t2: 
				self.t2.remove(key)
				
			self.t2.appendleft(key)
		elif key in self.b1:
			self.p = min(
			self.size, self.p + max(len(self.b2) / len(self.b1) , 1))
			self.replace(key)
			self.b1.remove(key)
			self.t2.appendleft(key)
		elif key in self.b2:
			self.p = max(0, self.p - max(len(self.b1)/len(self.b2) , 1))
			self.replace(key)
			self.b2.remove(key)
			self.t2.appendleft(key)   
		else:
			l1_size = len(self.t1) + len(self.b1)
			l2_size = len(self.t2) + len(self.b2)
			
			if l1_size == self.size:
				if len(self.t1) < self.size:
					self.b1.pop()
					self.replace(key)
				else:
					del self.cached[ self.t1.pop() ]
			elif l1_size < self.size and l1_size + l2_size >= self.size:
				if l1_size + l2_size == 2 * self.size:
					self.b2.pop()
				self.replace(key)
			
			self.t1.appendleft(key)
		
		self.cached[key] = item  
		
	def __len__(self):
		return len( self.cached )

	def items(self):
		return self.cached.items()
		
	def __contains__(self, key):
		return key in self.cached
		
class HybridCache(Cache):
	"""
	only str key
	cannot delete item, to preserve O(1) time complexity with cached
	"""
	def __init__(self, size, csize, mod=0, path="/tmp/"):
		""" stop insertion if size reached"""
		Cache.__init__(self, size)

		self.number 	= 0
		
		self.tmpDir		= tempfile.TemporaryDirectory(prefix=os.path.join(path, "hybriddict_") )
		self.data		= shelve.open( self.tmpDir.name+"/1" )
		self.cache 		= ARCCache( csize ) 
	
	def __del__(self):
		self.data.close()
	
	def __setitem__(self, key, item):
		#performance de shelve.__setitem__
		if  self.number >= self.size :
			return False
			
		tmp		= self.cache.__setitem__(key, item)

		self.data[key] 	= item
		
		self.number 	+= 1
		return True
	
	def __getitem__(self, key):
		#ici interet du cache
		item 	= self.cache[ key ]

		if isinstance(item, EmptyItem): 
			item = self.data[ key ]
		
		return item

	def __len__(self):
		return self.number
		
	def items(self):
		return self.data.items()
	
	def __contains__(self, key):
		return (key in self.cache) or (key in self.data)
