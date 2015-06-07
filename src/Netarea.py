from urllib.parse import urlparse, urljoin
from hashlib import md5
from .AVL import *

MAX = 1<<384
def Phi( urlRecord ): # 384bits
	urlObj = urlparse( urlRecord.url )

	scheme_md5 = md5(urlObj.scheme).hexdigest()
	netloc_md5 = md5(urlObj.netloc).hexdigest()
	url_md5	   = md5(urlRecord.url).hexdigest()
	
	return scheme_md5+netloc_md5+url_md5 # lexicographorder first on schem then netloc and finally url


class NetareaTree( AVL ):
	def __init__(self):
		AVL.__init__(self)
	
	def search(self, netarea):
		"""
			 @return the left closest area 
		"""
		if self.root == None:
			raise EmptyAVL
		
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
	def __init__(self, netarea="", value=None, left=None, right=None):
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
		self.used_ram = wheight
		self.max_ram = maxWeight
	
	def load(self):
		return float(self.max_ram-load_ram)/self.max_ram
		
	def is_overload(self):
		return self.load()>0.95

class NetareaReport(Report):
	"""
		@param netarea uniqu id (str)
		@param weight = plus c'est grarnad plus la partition est importante : servira à l'allouer à un Netareamanger robuste load balancibg
	"""
	def __init__(self, netarea, used_ram, max_ram, int_next_netarea=MAX):
		#netarea is an hash ie heaxdigit str
		self.netarea = netarea # [netarea,next_netarea[
		self.next_netarea = hex( int_next_netarea )
		self.int_netarea = int(netarea,16)
		self.int_next_netarea = int_next_netarea
		self.used_ram = used_ram
		self.max_ram = max_ram

	def split(self):
		mid = floor( (int_next_netarea-int_netarea) / 2.0 )
		
		self.used_ram = 0
		self.next_netarea = hex( mid) 
		self.int_next_netarea = mid
		
		return NetareaReport( hex(mid), 0, self.max_ram, int_next_netarea )

class MasterReport(Report):
	def init(self, ip, num_core, max_ram, maxNumNetareas, netarea_reports):
		self.ip				= ip
		self.num_core		= num_core
		self.max_ram		= max_ram
		self.maxNumNetareas	= maxNumNetareas
		self.netarea_reports= netarea_reports
	
	def is_overload(self):
		return self.maxNumNetareas <= len( self.netarea_reports)
	
	def allocate(self, net):
		self.netarea_reports.append( net )
