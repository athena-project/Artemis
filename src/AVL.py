class EmptyAVL( Exception ):
	pass

class AlreadyExists(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class AVL:
	def __init__(self):
		self.number = 0
		self.root = None
		
	def __setitem__(self, key, item):
		self.add( AVLNode(key, item) )
		
	def hight(self):
		return -1 if self.root==None else self.root.hight
		
	def empty(self):
		return self.root==None
		
	def add(self, node):
		if self.root != None:
			self.root.add(node)
		else:
			self.root = node
		self.number +=1
		
	def __getitem__(self, key):
		return self.get(key)
		
	def get(self, key):
		if self.root == None :
			raise EmptyAVL
		
		return self.root.get(key)
		
	def __str__(self):
		if self.root:
			return "Nodes : "+str(self.number)+"\n"+self.root.str(0)
		else:
			return "Empty AVL"
		
	def update(self, avlB):
		self.number = avlB.number
		self.root 	= avlB.root
			
	def suppr(self, key):
		if self.number == 1 and self.root.key == key:
			self.root = None
		else:
			self.root.suppr( key, self.root)
		self.number-=1
		
	
class AVLNode:#see Yves le maire exo6.3 AVL
	def __init__(self, key="", value=None, left=None, right=None):
		self.key = key
		self.value = value
		
		self.left 	= left
		self.right 	= right
		self.update()
		
	def update(self):
		self.d	= (-1 if self.right ==None else self.right.hight) 
		self.d -= (-1 if self.left ==None else self.left.hight)  #desequilibre
		self.hight= max( (-1 if self.right ==None else self.right.hight), 
			(-1 if self.left ==None else self.left.hight) )+1

	def __gt__(self, node):
		return self.key > node.key

	def __lt__(self, node):
		return self.key < node.key
		
	def str(self,i):
		space = "  "*i
		buff= space+"Key : "+str(self.key)+"\n"
		buff+= space+"Value : "+str(self.value)+"\n"
		buff+= space+"Hight :"+str(self.hight)+"\n"
		buff+= space+"D :"+str(self.d)+"\n"
		if( self.left != None ):
			buff+= space+"Left :\n"+self.left.str(i+1)+"\n"
		if( self.right != None ):
			buff+= space+"Right :\n"+self.right.str(i+1)+"\n"
		return buff
	
	def rotate_right(self):
		if self.left == None:
			return 
			
		left_node = self.left.left
		right_node= AVLNode( self.key, self.value, self.left.right, self.right)
		
		self.key = self.left.key
		self.value =  self.left.value
		self.left = left_node
		self.right = right_node
		
		self.update()
		
	def rotate_left(self):
		if self.right == None:
			return 
			
		left_node= AVLNode( self.key, self.value, self.left, self.right.left)
		right_node= self.right.right
		
		self.key = self.right.key
		self.value =  self.right.value
		self.left = left_node
		self.right = right_node

		self.update()
	
	def rotate_left_right(self):
		if self.left == None or self.left.right==None:
			return
		
		left_node = AVLNode( self.left.key, self.left.value, self.left.left, self.left.right.left)
		right_node= AVLNode( self.key, self.value, self.left.right.right ,self.right)
		
		
		self.key = self.left.right.key
		self.value =  self.left.right.value
		self.left = left_node
		self.right = right_node
		
		self.update()
		
	def rotate_right_left(self):
		if self.right == None or self.right.left==None:
			return
			
		left_node = AVLNode( self.key, self.value, self.left, self.right.left.left)
		right_node= AVLNode( self.right.key, self.right.value, self.right.left.right, self.right.right)
		
		self.key = self.right.left.key
		self.value =  self.right.left.value
		self.left = left_node
		self.right = right_node

		self.update()
	 	
	def balance(self):
		"""
			@brief balance the avl if right and left have already been  balanced 
		"""
		if self.d == -2 :
			if self.left.d == 1:
				self.rotate_left_right()
			else :
				self.rotate_right()
		elif self.d ==2 :
			if self.right.d == -1:
				self.rotate_right_left()
			else :
				self.rotate_left()
			
	def add(self, new_node):
		if new_node <  self :
			if self.left == None :
				self.left = new_node
			else:
				self.left.add( new_node )
		elif  new_node.key == self.key :
			raise AlreadyExists(key)
		else :
			if self.right == None :
				self.right = new_node
			else:
				self.right.add( new_node )
		self.update()
		self.balance()

	def get(self, key):
		if self.key == key :
			return self.value
		elif key< self.key:
			return self.left.get(key)
		else :
			return self.right.get(key)
		
	def suppr_min(self):
		if self.left == None:
			right = self.right
			return (self, right)
		else :
			node, right_node = self.left.suppr_min() #node est le plus petit
			
			self.left = right_node
			self.update()
			self.balance()
			return node, self
			
	def erase(self, node):
		if node.key<self.key:
			self.left = None
		else:
			self.right = None
			
	#current parent du pere pointant sur le fils courabnt
	def suppr(self, key, parent):
		if key<self.key:
			self.left.suppr(key, self)
		elif  key>self.key:
			self.right.suppr(key, self)
		else:
			if self.right == None and self.left == None:
				parent.erase( self )
				return
			
			if self.right == None:
				self.key= self.left.key
				self.value = self.left.value
				self.right = self.left.right
				self.left = self.left.left

				del self.left
			else:
				node, right_node = self.right.suppr_min()
				self.key = node.key
				self.value = node.value
				self.right = right_node
		self.update()
		self.balance()	
		
	def search(self, key):
		if self.key == key :
			return self.value
		elif key < self.key :
			if self.left != None :
				return self.left.search(key)
			else :
				return self.value 
		else :
			if self.right != None :
				return self.right.search(key)
			else :
				return self.value	

	def next(self, key, parent=None):
		"""
		first >=key
		"""
		if self.key == key :
			return self.value
		elif key < self.key :
			if self.left != None :
				return self.left.next(key, self)
			elif self.right != None:
				return self.value  
		else :
			if self.right != None :
				return self.right.next(key, self)
			else :
				return self.parent	#min right	
