from hashlib import md5
from collections import UserList

MAX = int("f"*64, base=16)
def Phi( task ): # 224bytes
	netloc_md5 = int( md5(task.netloc.encode('utf-8')).hexdigest(), base=16)
	url_md5	   = int( md5(task.url.encode('utf-8')).hexdigest(), base=16)
	
	return (netloc_md5<<128)+url_md5 # lexicographorder first on schem then netloc and finally url

class NetRing(UserList):
	def __init__(self, netareas=[]):
		self.hydrate(netareas)
		
	def hydrate(self, netareas):
		self.data = netareas
		self.data.sort()
		
	def update(self, netareas):
		self.hydrate(netareas)
		
	def set(self, net_ring):
		self.data = net_ring.data
	
	def __getitem__(self, key):
		self.data[ key % len(self.data) ]
		
	def __setitem__(self, key, item):
		self.data[ key % len(self.data) ] = item

	def __delitem__(self, key):
		del self.data[ key % len(self.data) ]
	
