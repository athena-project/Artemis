import os
from time import sleep, time as t_time

from .Netarea import *
from .Task import Task, TaskNature, AVERAGE_TASK_SIZE

from .Robot import RobotCache
from threading import Thread, RLock, Event
from multiprocessing import Process, Queue, Value
from copy import deepcopy
from collections import deque

from .Utility import serialize, unserialize
from .Cache import ARCCache, HybridCache

from .network.Msg import MsgType, Msg
from .network.TcpServer import T_TcpServer, P_TcpServer, TcpServer
from .network.TcpClient import TcpClient
from .network.Reports import MasterReport, MonitorReport

import logging
from termcolor import colored

TASK_BUNDLE_LEN = 20 #task
FAST_CONF		= True #on utilise ARCCache au lieu d'hybride( all in ram) 

class Master():
	"""
		@param maxRam used by this server
		@param maxCore max core used by this server
	"""
	def __init__(self, host, monitors, useragent, delay, maxNumNetareas, 
	maxRamNetarea):
		self.monitors			= monitors
		self.num_cores			= os.cpu_count()
		self.maxRam				= maxNumNetareas * maxRamNetarea 
				
		self.useragent			= useragent
		self.delay				= delay
		
		self.maxNumNetareas		= maxNumNetareas
		self.maxRamNetarea		= maxRamNetarea
		
		self.pool				= []
		
		self.MasterServer_Exit	= Event()
		

		self.out_workers		= 2
		
		self.netarea_reports	= {}
		self.shared_values		= {}
		
		self.monitors_lock					= RLock()
		self.netarea_reports_lock			= RLock()
		
		self.masterServer		= MasterServer(
			host,
			self, 
			self.monitors, 
			self.netarea_reports, 
			self.MasterServer_Exit,
			self.monitors_lock,
			self.netarea_reports_lock)
			
		self.host				= self.masterServer.get_host()
		self.port				= self.masterServer.port
		self.client				= TcpClient()
		logging.debug("Master initialized")

	def start_netareamanager(self, netarea):
		maxInTasksSize	= int( 0.03 * self.maxRamNetarea )# 1<<22	#maxInTasksSize 4Mb
		maxDoneTasksSize= int( 0.02 * self.maxRamNetarea )# 1<<22	#maxDoneTasksSize 4Mb
		maxOutTasksSize	= int( 0.02 * self.maxRamNetarea )# 1<<22	#maxOutTasksSize 4Mb
		maxRobotsSize	= int( 0.03 * self.maxRamNetarea )# 1<<22 #maxRobotsSize 4Mb
		maxTasksMapSize	= int( 0.90 * self.maxRamNetarea )# maxTaskMapsSize 128Mb
				
				
		shared_used_ram	= Value('i', 0)
		s = NetareaManager( self.host, netarea.netarea, self.out_workers, 
			maxInTasksSize, maxDoneTasksSize, maxOutTasksSize, 
			self.useragent, self.delay, maxTasksMapSize, 
			maxRobotsSize, shared_used_ram)
		
		if s :
			netarea.port	= s.port
			with self.netarea_reports_lock :
				self.netarea_reports[ netarea.netarea ] = netarea 
			self.shared_values[ netarea.netarea ] = shared_used_ram
			self.pool.append( s )
			
			s.start()
			logging.info("New netarea %s %s" % (netarea.netarea, 
				(colored('%d', 'red', attrs=['reverse', 'blink']) % netarea.port)))
		else:
			logging.error("Can not setup netarea : %s" % netarea.netarea)
		
	def terminate(self):
		self.MasterServer_Exit.set()
		for netareaManager in self.pool:
			netareaManager.terminate() if netareaManager.is_alive() else () 
		logging.info("NetareaManagers stoped")
	
	def harness(self):
		self.masterServer.start()
		while True:
			with self.netarea_reports_lock:
				netarea_reports = deepcopy( self.netarea_reports ).values()
			
			netarea_reports = list( netarea_reports ) 
			for report in netarea_reports:
				report.used_ram = self.shared_values[ report.netarea ].value
			
			
			report = MasterReport( self.host, self.port, self.num_cores,
				self.maxRam, self.maxNumNetareas, netarea_reports ) 
			
			with self.monitors_lock:
				for (m_host, m_port) in self.monitors:
					self.client.send( 
						Msg( MsgType.ANNOUNCE_MASTER, report), 
						m_host, 
						m_port) 

			sleep(1)
			
class MasterServer(T_TcpServer):
	def __init__(self, host, parent, monitors, netarea_reports, Exit,
	monitors_lock, netarea_reports_lock):
		T_TcpServer.__init__(self, host, Exit)
				
		self.parent					= parent
		self.monitors				= monitors
		self.netarea_reports		= netarea_reports
		self.Exit 					= Exit
		self.monitors_lock			= monitors_lock
		self.netarea_reports_lock	= netarea_reports_lock
		
		logging.info( "MasterServer initialized")
		
		
	def callback(self, data):
		msg	= TcpServer.callback(self, data)
		
		if msg.t == MsgType.ANNOUNCE_NETAREA_UPDATE :
			with self.netarea_reports_lock :
				for net in msg.obj[1]: #modified
					self.netarea_reports[ net.netarea ].next_netarea= net.next_netarea
					self.netarea_reports[ net.netarea ].used_ram 	= 0 
					
				for net in msg.obj[0]: #add
					self.parent.start_netareamanager( net )	
		elif msg.t == MsgType.ANNOUNCE_MONITORS:
			with self.monitors_lock:
				self.monitors.clear()
				self.monitors.update( msg.obj )
		else:
			logging.info("Unknow received msg %s" % msg.pretty_str())
			
class NetareaManager(P_TcpServer):
	"""
		Warning : One netareamanager by netarea on the whole network
	"""
	def __init__(self, host, net_area, out_workers, maxInTasksSize, 
	maxDoneTasksSize, maxOutTasksSize, useragent, delay, maxTasksMapSize, 
	maxRobotsSize, shared_used_ram) :
		"""
			@param netarea			- netarea hash
			@param useragent		- 
			@param delay			- period between two crawl of the same page
			@param maxRamSize		- maxsize of the tasks list kept in ram( in Bytes )
			@param numOverseer		- 
		"""
		P_TcpServer.__init__(self, '')
		
		self.slaveMap			= {}
		
		self.in_tasks			= deque( maxlen=maxInTasksSize )
		self.done_tasks			= deque( maxlen=maxDoneTasksSize )
		self.out_tasks			= deque( maxlen=maxOutTasksSize )
		
		self.shared_used_ram	= shared_used_ram
		
		self.Exit				= Event()
		self.InExit				= Event()
		self.ValidatorExit		= Event()
		self.DoneExit			= Event()
		self.OutExit			= Event()
		
		self.slaves_lock		= RLock()
		
		self.validator			= Validator(useragent, delay,
			maxTasksMapSize, maxRobotsSize, self.in_tasks, 
			self.done_tasks, self.out_tasks, self.shared_used_ram, 
			self.ValidatorExit )	
		self.out_pool			= [ 
			Out_Worker(self.slaveMap, self.out_tasks, self.OutExit, 
				self.slaves_lock ) 
			for k in range(out_workers) ]
			
	def terminate(self):		
		self.ValidatorExit.set()
		while self.validator and self.validator.is_alive():
			sleep(0.1)
		
		self.OutExit.set()
		while self.out_pool :
			for w in self.out_pool:
				self.out_pool.remove( w ) if not w.is_alive() else ()
			sleep(0.1) if self.out_pool else () 
			
		P_TcpServer.terminate(self)
	
	def run(self):
		self.validator.start()
		
		for w in self.out_pool:
			w.start()
			
		P_TcpServer.run(self)
		
	def callback(self, data):
		msg	= TcpServer.callback(self, data)		

		if msg.t == MsgType.MASTER_IN_TASKS:
			self.in_tasks.append( msg.obj )
		elif msg.t == MsgType.MASTER_DONE_TASKS:
			self.done_tasks.append( msg.obj )
		elif msg.t == MsgType.ANNOUNCE_SLAVE_MAP:
			with self.slaves_lock:
				self.slaveMap.clear()
				self.slaveMap.update( msg.obj )	
		elif msg.t == MsgType.ANNOUNCE_DELTA_SLAVE_MAP:
			with self.slaves_lock:
				for slave in msg.obj[1]: #deletion first
					del self.slaveMap[ slave.id() ]
				for slave in msg.obj[0]:
					self.slaveMap[ slave.id() ] = slave
		else:
			logging.info("Unknow received msg %s" % msg.pretty_str())

class Validator( Thread ):
	"""
		@brief One validator per Server
	"""
	def __init__(self, useragent, delay, maxTasksMapSize, maxRobotsSize,
		in_tasks, done_tasks, out_tasks, shared_used_ram, Exit) :
		"""
			@param useragent		- 
			@param period			- period between to wake up
			@param delay			- default period between two crawl of the same page
			@param maxRamSize		- maxsize of the tasks list kept in ram( in Bytes )
			@param in_tasks			- tasks incomming
			@param done_tasks		- tasks crawled
			@param out_tasks			processed tasks
			@shared_used_ram		- multiprocessin value
		"""
		Thread.__init__(self)
		
		self.useragent 			= useragent
		self.delay				= delay # de maj
			
		self.maxTasksMapSize		= maxTasksMapSize
		self.maxRobotsSize		= maxRobotsSize
		
		if FAST_CONF:		
			self.tasksMap		= ARCCache( maxTasksMapSize ) 
		else:  
			self.tasksMap		= HybridCache( maxTasksMapSize*1024, 
				maxTasksMapSize)
				
		self.in_tasks			= in_tasks
		self.done_tasks			= done_tasks
		self.out_tasks			= out_tasks
		self.robotsMap			= RobotCache( maxRobotsSize, useragent )
		
		self.lastUpdate			= t_time()	
		
		self.shared_used_ram	= shared_used_ram
		self.Exit				= Exit
		
		logging.debug("Validator initialized")
		
	def is_valid(self, task):
		url = task.url
		if( url in self.tasksMap and  
		self.tasksMap[url].is_alive(self.delay) ):
			return False

		valid, sitemaps	= self.robotsMap.get( task )
		if sitemaps : # independant de permition d'acces
			self.in_tasks.append( sitemaps )
		if not valid: 
			return False

		if url in self.tasksMap : #merge
			if task.lastvisited != -1:
				task.lastvisited = task.lastvisited  
			else:
				task.lastvisited = self.tasksMap[url].lastvisited
			
			if task.lasthash != "":
				task.lasthash = task.lasthash  
			else:
				task.lasthash = self.tasksMap[url].lasthash
				
			if task.refreshrate != 1:
				task.refreshrate = task.refreshrate  
			else: 
				task.refreshrate = self.tasksMap[url].refreshrate

		task.lastcontrolled = t_time()
		self.tasksMap[url]=task
		return True
	
	def validate(self):
		while self.in_tasks :
			for task in  self.in_tasks.popleft():
				if self.is_valid( task ):
					self.out_tasks.append( task )
	
	def refresh(self):
		"""
			@brief Update the taskMap with done_tasks
		"""
		while self.done_tasks :
			task =  self.done_tasks.popleft()
			self.tasksMap[task.url] = task 
			
	def update(self): 
		"""
			@brief update of the map, ie maj of the task already store
		"""

		if self.lastUpdate	> t_time()-self.delay:
			return
		
		for (key,task) in self.tasksMap.items() :
			if task.nature != TaskNature.web_static_torrent and self.is_valid( task ):
				self.out_tasks.append( taskRecord )
				
		self.lastUpdate = t_time()	
		
	def run(self):
		while not self.Exit.is_set():
			self.refresh()
			self.validate()			
			self.update()
			
			#seul le nombre d'urls est interressant
			self.shared_used_ram.value	= len(self.tasksMap) 
			self.shared_used_ram.value *= AVERAGE_TASK_SIZE 
			
			sleep( 1 )
			
		#empty in_tasks
		self.refresh()
		self.validate()	

class Out_Worker( Thread ):
	def __init__(self, slaveMap, out_tasks, Exit, slaves_lock) :
		"""
			@param out_tasks			
		"""		
		Thread.__init__(self)
		
		self.slaveMap			= slaveMap
		self.out_tasks			= out_tasks
		self.Exit				= Exit
		self.slaves_lock		= slaves_lock
		
		self.client 			= None
		logging.debug("Out_Worker initialized")

		
	def add_tasks(self):
		while self.out_tasks and self.slaveMap:	#Round-Robin pondéré
			with self.slaves_lock: #obligé de le refaire à chaque fois( en cas de perte del'esclave entre temps)
				slaves = deepcopy( list(self.slaveMap.values()) )
			slaves.sort( key = (lambda x : x.load()) )
			
			for slave in slaves:
				tasks		= [] 
				
				try:
					for k in range( TASK_BUNDLE_LEN ) : 
						task = self.out_tasks.popleft()
						tasks.append( task )
				except Exception:
					pass

				if tasks:
					self.client.send(
						Msg( MsgType.SLAVE_IN_TASKS, tasks), 
						slave.host, slave.port )
			
	def run(self):
		self.client = TcpClient()

		while not self.Exit.is_set():
			self.add_tasks()
			sleep(1)
		
		#empty out_tasks
		URL_BUNDLE_LEN=1
		self.add_tasks()
