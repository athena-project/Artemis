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
	T_ACCEPTED 			= '1'
	T_ACCEPTED_SIZE		= 0
	T_DECO 				= '2'
	T_DECO_SIZE 		= 0
	T_DONE 				= '3'
	T_DONE_SIZE			= 0
	T_ID				= '4'
	T_ID_SIZE			= 0
	T_PENDING  			= '5'
	T_PENDING_SIZE		= 0
	T_PROCESSING		= '6'	
	T_PROCESSING_SIZE	= 0	
	T_RESEND			= '7'
	T_RESEND_SIZE		= 0
	T_URL_TRANSFER		= '8'
	T_URL_TRANSFER_SIZE	= 4096
	
	def getSize( s ):
		if s == TcpMsg.T_ACCEPTED:
			return TcpMsg.T_ACCEPTED_SIZE
		if s == TcpMsg.T_DECO:
			return TcpMsg.T_DECO_SIZE
		if s == TcpMsg.T_DONE:
			return TcpMsg.T_DONE_SIZE
		if s == TcpMsg.T_ID:
			return TcpMsg.T_ID_SIZE
		if s == TcpMsg.T_PENDING:
			return TcpMsg.T_PENDING_SIZE
		if s == TcpMsg.T_PROCESSING:
			return TcpMsg.T_PROCESSING_SIZE
		if s == TcpMsg.T_RESEND:
			return TcpMsg.T_RESEND_SIZE
		if s == TcpMsg.T_URL_TRANSFER:
			return TcpMsg.T_URL_TRANSFER_SIZE
		
		return 0
	
class TcpMsgHandler:
	"""
	"""
	def __init__(self):
		pass
		
	def serializeUrl(self, d):
		return d['url']+"|"+d['alt']+"|"+d['charset']+"|"+d['type']
			
	def make( urls ):
		msgs= []
		size = 0
		tmpSize = 0
		i=0
		
		for url in urls:
			tmpSize= 3+url['url'] +3+url['alt']+7+url['charset']+4+url['type']
			if( size == 0):
				msgs.append( T_URL_TRANSFER )
				i+=1
				
			if( tmpSize + size < TcpMsg.T_URL_TRANSFER_SIZE ):
				size += tmpSize
				msgs[i]+="||"+serializeUrl(url)+"||"
				
			else:
				size=tmpSize
				i+=1
				msgs.append( T_URL_TRANSFER+"||"+serializeUrl(url)+"||" )
		return msgs
