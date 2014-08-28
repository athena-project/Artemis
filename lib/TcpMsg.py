import pickle

class TcpMsg:
	"""
	
		Const : 
			T_ACCEPTED 		identification accepted 		( send by server )
			T_DECO 			deco 							( send by slave )
			T_DONE 			end of the current transaction	( send by both )
			T_ID			connection request				( send by slave )
			T_PENDING  		pending to work					( send by slave )
			T_PROCESSING	processing the current task		( send by slave )
			T_RESEND		last msg request				( send by both )
			T_URL_TRANSFER									( send by both )
	
	"""
	T_ACCEPTED 		= 1
	T_DECO 			= 2
	T_DONE 			= 3
	T_ID			= 4
	T_PENDING  		= 5
	T_PROCESSING	= 6	
	T_RESEND		= 7
	T_URL_TRANSFER	= 8
	
	
	
	
	def __init__(self, t, s=0, d=""):
		self.type=t;
		self.size=s;
		self.data=d;
		
	def serialize(self):
		return pickle.dumps( self )
	

