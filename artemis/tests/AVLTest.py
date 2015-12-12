import unittest
from random	import randint
from artemis.AVL import AVL

class AVLTest(unittest.TestCase):
	def test_avl_insertion(self):
		tree = AVL()
		d={}
		d["0"]=0
		tree["0"]=0
		for k in range(10000):
			tmp = str(randint(0, 1<<30))
			if tmp not in d:
				tree[tmp]=1 
				d[tmp]=True
				
			self.assertTrue(  tree.root.d<3 , str(tree.root.d)+"  "+str(k) )
	def test_avl_get(self):
		tree = AVL()
		d={}
		d["0"]=0
		tree["0"]=1
		for k in range(10000):
			tmp = str(randint(0, 1<<30))
			if tmp not in d:
				tree[tmp]=1 
				d[tmp]=True
				
			self.assertTrue(  tree[tmp]==1 , str(k)+"  "+str(tree[tmp]) )
