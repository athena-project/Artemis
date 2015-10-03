from urllib.parse import urlparse, urljoin
from hashlib import md5
from .AVL import *
import time

LIFETIME		=	2#s report liftime x2 slower than sending

MAX = int("f"*64, base=16)
def Phi( task ): # 384bits
	netloc_md5 = int( md5(task.netloc.encode('utf-8')).hexdigest(), base=16)
	url_md5	   = int( md5(task.url.encode('utf-8')).hexdigest(), base=16)
	
	return netloc_md5*(10**32)+url_md5 # lexicographorder first on schem then netloc and finally url

class NetareaTree( AVL ):
	def __init__(self):
		AVL.__init__(self)
	
	def search(self, netarea):
		"""
			 @return the left closest area 
		"""
		if self.root == None:
			raise Exception("EmptyAVL")
		
		return self.root.search( netarea )
	
	def next(self, netarea):
		"""
			first >=netarea
		"""
		if self.root == None:
			raise EmptyAVL
		
		return self.root.next( netarea, root )
		
	def __setitem__(self, key, item):
		self.add( NetareaNode(key, item) )
		
class NetareaNode(AVLNode):
	def __init__(self, netarea=0, value=None, left=None, right=None):
		AVLNode.__init__(self,netarea, value, left, right)
		
	def search(self, netarea):
		if self.key == netarea :
			return self.value
		elif netarea < self.key :
			if self.left != None :
				return self.left.search(netarea)
			else :
				return self.value 
		else :
			if self.right != None :
				return self.right.search(netarea)
			else :
				return self.value	

	def next(self, netarea, parent=None):
		"""
		first >=netarea
		"""
		if self.key == netarea :
			return self.value
		elif netarea < self.key :
			if self.left != None :
				return self.left.next(netarea, self)
			elif self.right != None:
				return self.value  
		else :
			if self.right != None :
				return self.right.next(netarea, self)
			else :
				return self.parent	#min right




class Report:
	def __init__(self, used_ram, max_ram):
		self.used_ram = used_ram
		self.max_ram = max_ram
		
		self.expires	= time.time() + LIFETIME
	
	def load(self):
		return float(self.used_ram)/self.max_ram
		
	def is_overload(self):
		return self.load()>0.95
		
	def is_expired(self):
		return time.time() > self.expires

class NetareaReport(Report):
	"""
		@param netarea uniqu id (str)
		@param weight = plus c'est grarnad plus la partition est importante : servira à l'allouer à un Netareamanger robuste load balancibg
	"""
	def __init__(self, netarea, used_ram, max_ram, next_netarea=MAX):
		#netarea is an hash ie heaxdigit str
		self.netarea = netarea # [netarea,next_netarea[
		self.next_netarea = next_netarea
		Report.__init__(self, used_ram, max_ram)
		
	def split(self):
		mid = floor( (next_netarea-netarea) / 2.0 )
		
		self.used_ram = 0
		self.next_netarea = mid
		
		return NetareaReport(mid, 0, self.max_ram, next_netarea )

class MasterReport(Report):
	def __init__(self, id, num_core, max_ram, maxNumNetareas, netarea_reports):
		self.id				= id
		self.num_core		= num_core
		self.maxNumNetareas	= maxNumNetareas
		self.netarea_reports= netarea_reports
		
		Report.__init__(self, 0, max_ram)
	
	def is_overload(self):
		return self.maxNumNetareas <= len( self.netarea_reports)
	
	def allocate(self, net):
		self.netarea_reports.append( net )

	def __str__(self):
		return "id = "+str(self.id)+"\n"+"num_core = "+str(self.num_core)+"\nnetareas = "+str(len(self.netarea_reports))+"/"+str(self.maxNumNetareas)
