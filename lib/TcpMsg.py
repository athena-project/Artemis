import pickle

class TcpMsg:
	"""
	
		Const : 
			T_ACCEPTED 		identification accepted 		( server )
			T_DECO 			deco 							( slave )
			T_DONE 			end of the current transaction	( both )
			T_ID			connection request				( slave )
			T_PENDING  		pending to work					( slave )
			T_PROCESSING	processing the current task		( slave )
			T_RESEND		last msg request				( both )
			T_URL_TRANSFER									( both )
	
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
	

