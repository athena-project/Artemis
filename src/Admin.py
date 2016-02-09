from time import sleep
from .network.TcpClient import TcpClient
from .network.Msg import Msg, MsgType
from .network.TcpServer import T_TcpServer, TcpServer
from .network.Reports	import NetareaReport, MonitorReport
from .AVL import AVL
import logging
from threading import Lock, Thread, Event

from artemis.Utility import unserialize

class AdminServer(T_TcpServer):
	def __init__(self, host, monitors, slaveReports, masterReports, netTree,
	slaveMetrics, monitors_lock, slaves_lock, masters_lock, netTree_lock, 
	slaveMetrics_lock, Exit):
		
		
		self.monitors		= monitors
		self.slaveReports	= slaveReports
		self.masterReports	= masterReports
		self.netTree		= netTree
		self.slaveMetrics	= slaveMetrics
		
		self.monitors_lock	= monitors_lock
		self.slaves_lock	= slaves_lock
		self.masters_lock	= masters_lock
		self.netTree_lock 	= netTree_lock
		self.slaveMetrics_lock = slaveMetrics_lock
		
		T_TcpServer.__init__(self, host, Exit)
		
	def callback(self, data):
		msg	= TcpServer.callback( self, data)

		if msg.t == MsgType.metric_monitor :
			with( self.monitors_lock and self.slaves_lock 
			and self.masters_lock and self.netTree_lock ):
				self.monitors.update( msg.obj[0] )
				self.slaveReports.update( msg.obj[1] )
				self.masterReports.update( msg.obj[2] )
				self.netTree.update( msg.obj[3] )
		elif msg.t == MsgType.metric_slave:
			with self.slaveMetrics_lock:
				self.slaveMetrics[ msg.obj.id() ] = msg.obj
		else:
			logging.info("Unknow received msg %s" % msg.pretty_str())
			
class AdminClient:
	def __init__(self, host, monitors):
		self.monitors 		= monitors
		self.slaveReports	= {}
		self.masterReports	= {}
		self.netTree		= AVL()
		self.slaveMetrics	= {} 
		
		self.monitors_lock	= Lock()
		self.slaves_lock	= Lock()
		self.masters_lock	= Lock()
		self.netTree_lock	= Lock()
		self.slaveMetrics_lock	= Lock()
		
		self.Exit 			= Event()
		
		self.server 		= AdminServer(
			host,
			self.monitors, self.slaveReports, self.masterReports, 
			self.netTree, self.slaveMetrics, self.monitors_lock, 
			self.slaves_lock, self.masters_lock, self.netTree_lock, 
			self.slaveMetrics_lock, self.Exit)
			
		self.host			= self.server.get_host()
		self.port			= self.server.port
		self.client 		= TcpClient()
		
		self.server.start()
		logging.info("Admin initiallized")

	def __del__(self):
		self.Exit.set()	
	
	def refresh_monitors(self):
		with self.monitors_lock:
			for mon in self.monitors.values():
				self.client.send( Msg( MsgType.metric_expected, 
					(self.host, self.port) ), mon.host, mon.port)
	
	def refresh_slaves(self):
		with self.slaves_lock:
			for slave in self.slaveReports.values():
				self.client.send( Msg( MsgType.metric_expected, 
					(self.host, self.port) ), slave.host, slave.port)

	def refresh(self):
		self.slaveReports.clear()
		self.masterReports.clear()
		self.netTree.update( AVL() )
		self.slaveMetrics.clear()
		
		self.refresh_monitors()
		self.refresh_slaves()
		
	def print_slaves_results(self):
		print("Slaves balance sheet")
		
		with self.slaves_lock:
			for report in self.slaveReports.values():
				print( report )
				
	def print_slaves_metrics(self):
		print("Slaves metrics balance sheet")
		
		with self.slaveMetrics_lock:
			for report in self.slaveMetrics.values():
				print(report)
		
	def print_monitors_results(self):
		print("Monitors balance sheet")
		
		with self.monitors_lock:
			for report in self.monitors.values():
				print( report )
				
	def print_masters_results(self):
		print("Masters balance sheet")
		
		with self.masters_lock:
			for report in self.masterReports.values():
				print( report )
	
	def print_netTree(self):
		print("NetTree balance sheet")
		
		with self.netTree_lock:
			print(self.netTree)
			

#class AdminDaemon(Thread):
	#def __init__(self, monitors, Exit):
		#Thread.__init__(self)
		
		#self.monitors 		= monitors
		#self.slaveReports	= {}
		#self.masterReports	= {}
		#self.netTree		= AVL()
		#self.slaveMetrics	= {} #elmt (nbr_url, intervalle)
		
		#self.monitors_lock	= Lock()
		#self.slaves_lock	= Lock()
		#self.masters_lock	= Lock()
		#self.netTree_lock	= Lock()
		#self.slaveMetrics_lock	= Lock()
		
		#self.Exit 			= Exit
		
		#self.server 		= AdminServer(
			#self.monitors, self.slaveReports, self.masterReports, 
			#self.netTree, self.slaveMetrics, self.monitors_lock, 
			#self.slaves_lock, self.masters_lock, self.netTree_lock, 
			#self.slaveMetrics_lock, self.Exit)
			
		#self.host			= self.server.get_host()
		#self.port			= port
		#self.client 		= TcpClient()
		#logging.info("Admin initiallized")
	
	#def refresh_monitors(self):
		#with self.monitors_lock:
				#for mon in self.monitors:
					#self.client.send( Msg( MsgType.metric_expected, 
						#(self.host, self.port) ), mon.host, mon.port)
	
	#def refresh_slaves(self):
		#with self.slaves_lock:
				#for slave in self.slaves:
					#self.client.send( Msg( MsgType.metric_expected, 
						#(self.host, self.port) ), slave.host, slave.port)

	#def run(self):
		#while not self.Exit.is_set():
			#sleep(1)
		#logging.info("Admin stopped")
