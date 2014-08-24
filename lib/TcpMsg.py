import pickle 
import io
import copy

class TcpMsg:
	"""
	
	"""
	
	def __init__(self):
		self.type=0;
		self.size=0;
		self.data=0;
		
	def serialize(self):
		output = io.BytesIO()
		pickle.dump( self, output, pickle.DEFAULT_PROTOCOL )
		return output
	
t = TcpMsg()
g =t.serialize()
g.flush()

ff = copy.deepcopy(g) 	
s = pickle.load( g )
print( s.data )
		
