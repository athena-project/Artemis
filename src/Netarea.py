from urllib.parse import urlparse, urljoin
from hashlib import md5
from .AVL import AVL, EmptyAVL, AVLNode
import time

MAX = int("f"*64, base=16)
def Phi( task ): # 224bytes
	netloc_md5 = int( md5(task.netloc.encode('utf-8')).hexdigest(), base=16)
	url_md5	   = int( md5(task.url.encode('utf-8')).hexdigest(), base=16)
	
	return netloc_md5*(1<<128)+url_md5 # lexicographorder first on schem then netloc and finally url

class NetareaTree( AVL ):
	def __init__(self):
		AVL.__init__(self)
	
	def search(self, netarea):
		"""
			 @return the left closest area 
		"""
		if self.root == None:
			raise EmptyAVL()
		
		return self.root.search( netarea )
	
	def next(self, netarea):
		"""
			first >=netarea
		"""
		if self.root == None:
			raise EmptyAVL()
		
		return self.root.next( netarea, root )
	
	def update_netarea(self, netarea):
		node = self.get(netarea.netarea)
		node.port   	= netarea.port
		node.used_ram	= netarea.used_ram
		node.max_ram	= netarea.max_ram
		
	def __setitem__(self, key, item):
		self.add( AVLNode(key, item) )
		
class NetareaNode(AVLNode):
	def __init__(self, netarea=0, value=None, left=None, right=None):
		AVLNode.__init__(self,netarea, value, left, right)
		
