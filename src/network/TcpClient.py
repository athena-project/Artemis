import  socket,ssl
import select
from .Msg import Msg
from threading import Thread, Event
from collections import deque
import logging	
from time import sleep
import logging

class Sender(Thread):
	timeout = 0.001

	def __init__(self, waiting, ignore, Exit):
		Thread.__init__(self)
		self.Exit 	= Exit
		
		self.ignore 			= ignore
		self.waiting			= waiting
		self.dataMap			= {}		
		
		self.context = ssl.create_default_context()
		self.context.load_cert_chain(certfile="/usr/local/certs/artemis/client.crt", keyfile="/usr/local/certs/artemis/client.key", password="none")
		self.context.load_verify_locations("/usr/local/certs/artemis/server.crt")
		self.context.verify_mode = ssl.CERT_REQUIRED
		self.context.check_hostname=False
		
		self.potential_readers  = []
		self.potential_writers	= []
		self.potential_errs		= []
	
	def add(self):
		while len( self.potential_writers) < 10 and self.waiting:
			data, host, port	= self.waiting.popleft()
			sock 	= self.context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=host, do_handshake_on_connect=False)
		
			self.dataMap[ hash(sock) ] = (data, host, port)
			self.potential_writers.append( sock )
		
	def run(self):
		while not self.Exit.is_set():
			ready_to_read, ready_to_write, in_error = select.select(
			  self.potential_readers,
			  self.potential_writers,
			  self.potential_errs,
			  self.timeout)
			  
			for sock in ready_to_write :
				try:
					key					= hash(sock)
					data, host, port	= self.dataMap[ key ]
					sock.connect((host, port))
					
					if( len(data) != sock.send( data )):#bytes(data, 'utf-8')) ):
						logging.info(str(e))
					sock.shutdown(socket.SHUT_WR)
					sock.close()
				except Exception as e:
					if self.ignore :
						logging.info( "host=%s, port=%d, %s" % (host, port, e) )
					else:
						raise e
				finally:
					del self.dataMap[key]
					self.potential_writers.remove( sock )
					
			self.add()
				
class TcpClient:
	def __init__(self, ignore = True):	
		"""
			@param ignore error( only log then, False => exception)
		"""
		self.waiting			= deque() #(data, host, port)
		
		self.SenderExit 		= Event()
		self.sender				= Sender(self.waiting, ignore, self.SenderExit)
		
		self.sender.start()
	
	def terminate(self):
		self.SenderExit.set()
		while self.sender.is_alive():
			sleep(0.01)
	
	def send(self, msg, host, port):
		data	= msg.serialize()
		self.waiting.append( (data, host, port) )
		
