import select,socket,ssl, logging
from threading import Thread, RLock, Event
from .Msg import Msg
from artemis.Utility import unserialize
import logging
from multiprocessing import Process
import logging
from termcolor import colored
import sys, traceback

class PortNotFound(Exception):
	pass

class TcpServer(): 
	port		= 1571
	timeout 	= 0.001
	
	def __init__(self, host=''):
		"""
			must surcharge callback at least, and stop_function
		"""		
		self.host = host
		self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH) 
		self.context.load_cert_chain(certfile="/usr/local/certs/artemis/server.crt", keyfile="/usr/local/certs/artemis/server.key", password="none")
		self.context.load_verify_locations("/usr/local/certs/artemis/client.crt")
		self.context.verify_mode = ssl.CERT_REQUIRED

			
		self.stop_function	= lambda : True
		
		self.count = 0
		self.find_port()
	
	def get_host(self):
		"""return a valid host in order to connect the current server"""
		return socket.gethostbyname( socket.gethostname()) if self.host=='' else self.host
		
	def bind(self):
		self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.serversocket.bind((self.host, self.port))
		self.serversocket.setblocking(0)
		self.serversocket.listen(100)
		
		logging.info("Bind port : %s" % (
				(colored('%d', 'red', attrs=['reverse', 'blink']) % self.port)))
		
	def find_port(self):
		for k in range(10000):
			self.port += 1
			try:
				self.bind()
				return
			except Exception:
				pass
		raise PortNotFound()
		
	def callback(self, data):
		return unserialize( data )
		
	def run(self):
		potential_readers  	= [self.serversocket]
		potential_writers	= []
		potential_errs		= []

		while self.stop_function():
			try:
				ready_to_read, ready_to_write, in_error = select.select(
					potential_readers,
					potential_writers,
					potential_errs,
					self.timeout)
				
				for sock in ready_to_read :
					try:
						if sock == self.serversocket :
							(clientsocket, address) = self.serversocket.accept()			
							connstream = self.context.wrap_socket(clientsocket, server_side=True, do_handshake_on_connect=False)
							
							while True:
								try:
									connstream.do_handshake()
									break
								except ssl.SSLWantReadError:
									select.select([connstream], [], [])
								except ssl.SSLWantWriteError:
									select.select([], [connstream], [])
							
							potential_readers.append(connstream)
						else :
							try:
								data = sock.recv(2048)
							except ssl.SSLError as e:
								# Ignore the SSL equivalent of EWOULDBLOCK, but re-raise other errors
								if e.errno != ssl.SSL_ERROR_WANT_READ:
									raise
								continue
							
							# No data means end of file
							if not data:
								break
							#print("Data  = ", data)

							data_left = sock.pending()
							while data_left:
								data += sock.recv(data_left)
								data_left = sock.pending()
								
							self.callback(data)
							potential_readers.remove( sock )
							sock.shutdown(socket.SHUT_RDWR)
							sock.close()
					except Exception as e:
						logging.debug( traceback.extract_tb(sys.exc_info()[2]) + [str(e)])
						potential_readers.remove( sock )
						sock.shutdown(socket.SHUT_RDWR)
						sock.close()

			except Exception as e:
				logging.debug( traceback.extract_tb(sys.exc_info()[2]) + [str(e)])
				potential_readers  	= [self.serversocket]
				potential_writers	= []
				potential_errs		= []	
				
		self.serversocket.close()

class T_TcpServer(TcpServer,Thread):	
	def __init__(self, host, Exit):
		Thread.__init__(self)
		TcpServer.__init__(self, host)

		self.Exit 			= Exit
		self.stop_function	= lambda  : not self.Exit.is_set()
	
class P_TcpServer(TcpServer, Process):
	def __init__(self, host):
		Process.__init__(self)
		TcpServer.__init__(self, host)
