from urllib.parse import urlparse, urljoin
from hashlib import md5
from AVL import *

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
	def __init__(self, netarea, used_ram, max_ram):
		#netarea is an hash ie heaxdigit str
		self.netarea = netarea
		self.int_netarea = int(netarea,16)
		self.used_ram = wheight
		self.max_ram = maxWeight
		
	def split(self, coef, next_netarea):
		"""
			We assume that the repartition is uniform among url
		"""
		if netarea.load()<coef :
			return [self]
			
		num = ceil(self.load() / coef) 
		beg = netarea.netarea_int
		end = (next_netarea.netarea_int if next_netarea != None else MAX) 
		h = (end-beg)/num#pas
		
		return [ NetareaReport( hex(self.netarea_int+k*h), int(self.used_ram/num), self.max_ram ) for k in range(num)]

class MasterReport(Report):
	def init(self, ip, num_core, max_ram, netarea_reports):
		self.ip				= ip
		self.num_core		= num_core
		self.max_ram		= max_ram
		self.netarea_reports= netarea_reports
		
		self.calcul_used_ram()
		self.calcul_free_ram()
		
	def calcul_used_ram(self):
		self.used_ram=0 #allocated ram
		for netarea in netarea_reports:
			self.used_ram += self.netarea.max_ram
	
	def calcul_free_ram(self):
		self.free_ram=self.max_ram-self.used_ram

	def garbage_collector(self, coef):
		"""
			@param float [0,1]
		"""
		for netarea in netarea_reports:
			if netarea.load()<coef:
				n = (coef - netarea.load-0.1) 
				netarea.max_ram = (n * netarea.max_ram) if n>0 else netarea.max_ram
				
		last = self.used_ram
		self.calcul_used_ram()
		self.calcul_free_ram()
		return last != self.used_ram # s'il y a eu une modification => True 

#Monitor




#master_reports = list des reports recueillit par le reseau sans doublon
GLOBAL_LOADBALANCING = False

i=0
while i<len(master_reports) and not GLOBAL_LOADBALANCING:
	GLOBAL_LOADBALANCING = master_reports[i].is_overload()
	i+=1
	
#LOCAL_LOAD balancing
if not GLOBAL_LOADBALANCING:
	#overloadnetarea_master : master dont au moins une netarea est overload
	local_loadbalancing(0.5, overloadnetarea_master)
	
def local_loadbalancing(coef, master):
	overload_netareas = []
	for netarea in master.netarea_reports:
		ram_needed = (netarea.load()-coef) * netarea.max_ram
		if ram_needed <0:
			pass
		elif master.free_ram > ram_needed:
			netarea.max_ram	+= ram_needed
			master.calcul_used_ram()
			master.calcul_free_ram()
		elif master.garbage_collector():
			local_loadbalancing(coef, master)
		elif coef<0.8 :
			local_loadbalancing( coef+0.1, master )
		else:
			GLOBAL_LOADBALANCING = True

def global_loadbalancing_1(coef, master_reports):
	"""
		@return True : all netarea are allocated, False : global_loadbalancing_2 needed
		on ne realloue que ce qui nous gêne
	"""
	copy_master_reports = copy.deepcopy( master_reports )
	overload_netareas = []
	for master in copy_master_reports:
		master.garbage_collector(coef)
		
		for netarea in mastre.netarea_reports:
			if netarea.overload():
				overload_netareas.append( netarea )
				master.netarea_reports.suppr(netare)
				
		master.calcul_used_ram()
		master.calcul_free_ram()
		if master.free_ram > 0:
			free_masters.append(master)
			
	free_maters.sort(key=lambda master: -1*master.free_ram) 
	overload_netareas.sort(key=lambda netarea: -1*(1+netarea.load()-coef)*netarea.max_ram)
	
	for netarea in overload_netareas:
		needed_ram = (1+netarea.load()-coef) * netarea.max_ram
		if needed_ram < free_masters[0].free_ram :
			free_masters[0].netarea_reports.append( needed_ram )
			
			master.calcul_used_ram()
			master.calcul_free_ram()
			free_maters.sort(key=lambda master: -1*master.free_ram) 
		elif coef<0.8 :
			global_loadbalancing_1(coef+0.1, master_reports)
		else:
			return (False, master_reports)
			
	return (True, copy_master_reports)

def global_loadbalancing_2(coef, master_reports):
	netareas = []
	masters  = []
	global_max_ram = 0
	
	masters.append( copy.deepcopy(master) )
	masters[-1].netareas_reports = [] 
	
	needed_ram=0
	for netarea in netareas:
		needed_ram += (1+netarea.load()-coef) * netarea.max_ram
		
	#Si une solution peut être trouvée
	if needed_ram>global_max_ram:
		return (False, master_reports)
	
	netareas.sort(key=lambda netarea : -1*(1+netarea.load()-coef) * netarea.max_ram)
	netareas_n=netareas
	netarea_n.sort((key=lambda netarea :netarea.netarea)
	masters.sort(key=lambda master : -1*master.max_ram)
	
	#Allocation de la plus lourde netarea à master le plus robuste
	while netareas:
		netarea = netareas.pop()
		if 1+netarea.load()-coef) * netarea.max_ram < masters[0].max_ram : #on alloue
			masters[0].netareas_reports.append( netarea )
		else: #il faut decouper
			index = netareas_n.index( netarea) +1
			next_netarea = netareas_n[ index ] if index < len(next_netarea) else MAX
			netareas.extend( netarea.split( (1-coef) * masters[0].max_ram ,next_netarea ) )
		
		netareas.sort(key=lambda netarea : -1*(1+netarea.load()-coef) * netarea.max_ram) # ici on pourrait réinserer à la bonne place (dichotomie) pour eviter les trie
		masters.sort(key=lambda master : -1*master.max_ram)
	
	return (True, masters)

#On construit l'arbre à envoyer : 
for master in masters:
	for netarea in mast.netarea_reports:
		net_tree[netarea.netarea]=netarea


