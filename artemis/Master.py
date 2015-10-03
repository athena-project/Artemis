import sys
import collections
import os
from time import sleep, time as t_time
from .network.AMQPConsumer import *
from .network.AMQPProducer import *
from .Netarea import *


from .Mtype import *
from .Task import Task, TASK_WEB_STATIC_TORRENT

from .RobotCacheHandler import *
from threading import Thread, RLock, Event
from multiprocessing import Process, Queue


from .Utility import serialize, unserialize
from .LimitedCollections import LimitedDeque, HybridDict

from .Monitor import HEADER_NETAREA_PROPAGATION

import pdb

#os.setpriority
#os.cpu_count()
#os.getloadavg()

TASK_BUNDLE_LEN = 10 #task

class Master(AMQPConsumer):
	"""
		@param maxRam used by this server
		@param maxCore max core used by this server
	"""
	#ip					="127.0.0.1"
	#pool				= []
	#Monitor_out_Exit	= Event()
	
	def __init__(self, id="127.0.0.1", useragent="*",  domainRules={"*":False},
	protocolRules={"*":False}, originRules={"*":False}, delay = 36000,
	maxNumNetareas=2, maxRamNetarea=1<<27):
		AMQPConsumer.__init__(self)
		self.channel.exchange_declare(exchange='artemis_monitor_master_out', type='direct')
		self.channel.queue_bind(queue=self.key, exchange='artemis_monitor_master_out', routing_key=id)
		
		self.id					= id
		self.useragent			= useragent
		self.delay				= delay
		
		self.domainRules 		= domainRules
		self.protocolRules		= protocolRules
		self.originRules		= originRules
		
		self.maxNumNetareas		= maxNumNetareas
		self.maxRamNetarea		= maxRamNetarea
		
		self.pool				= []
		
		self.Monitor_out_Exit	= Event()
		
		self.in_workers			= 4
		self.done_workers		= 2
		self.out_workers		= 2
		
		self.netarea_reports	={}
		self.order = NetareaTree()
		
		self.monitor_out	= Monitor_out( self.id, os.cpu_count(), 0, self.maxNumNetareas, self.netarea_reports, self.Monitor_out_Exit)
		
		logging.debug("Master initialized")

	def start_netareamanager(self, netarea):
		#maxInTasksSize	= Mint(0.025 * self.maxRamNetarea) #1<<22	#maxInTasksSize 4Mb
		#maxDoneTasksSize	= Mint(0.025 * self.maxRamNetarea) #1<<22	#maxDoneTasksSize 4Mb
		#maxOutTasksSize	= Mint(0.025 * self.maxRamNetarea) #1<<22	#maxOutTasksSize 4Mb
		#maxRobotsSize	= Mint(0.025 * self.maxRamNetarea) #1<<22 #maxRobotsSize 4Mb
		#maxTasksMapSize	= Mint(0.900 * self.maxRamNetarea) #Mint(1<<27) #maxTaskMapsSize 128Mb
		
		#i think we do not need mutable int
		maxInTasksSize	= 0.025 * self.maxRamNetarea #1<<22	#maxInTasksSize 4Mb
		maxDoneTasksSize= 0.025 * self.maxRamNetarea #1<<22	#maxDoneTasksSize 4Mb
		maxOutTasksSize	= 0.025 * self.maxRamNetarea #1<<22	#maxOutTasksSize 4Mb
		maxRobotsSize	= 0.025 * self.maxRamNetarea #1<<22 #maxRobotsSize 4Mb
		maxTasksMapSize	= 0.900 * self.maxRamNetarea #Mint(1<<27) #maxTaskMapsSize 128Mb
				
		s = NetareaManager( netarea.netarea, self.in_workers, self.done_workers, self.out_workers, maxInTasksSize, maxDoneTasksSize, maxOutTasksSize, self.useragent, self.domainRules,
				self.protocolRules, self.originRules, self.delay, maxTasksMapSize, maxRobotsSize, netarea, self.order)
		
		if s :
			self.netarea_reports[ netarea.netarea ] = netarea 
			self.pool.append( s )
			
			s.start()
		else:
			logging.error("Can not setup netarea : "+netarea.netarea)
		
	def terminate(self):
		self.Monitor_out_Exit.set()
		for netareaManager in self.pool:
			netareaManager.terminate() if netareaManager.is_alive() else () 
		logging.info("NetareaManagers stoped")
	
	def harness(self):
		logging.debug("Master initialized")
			
		self.monitor_out.start()
		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while True:
			self.channel.wait()
	
	def proccess(self, msg):
		header, args	= unserialize( msg.body )
		AMQPConsumer.process( self, msg)
		
		if header == HEADER_NETAREA_PROPAGATION:
			(report, net_tree) 	= args
			self.order			= net_tree
			print("NetTree received ")

			for netarea in report.netarea_reports:
				print("net")
				if netarea.netarea in self.netarea_reports and netarea.next_netarea != self.netarea_reports[ netarea.netarea ]: #modified
					self.netarea_reports[ netarea.netarea ].next_netarea 		= netarea.next_netarea
					self.netarea_reports[ netarea.netarea ].used_ram 			= 0 					
				else :
					print("starting")
					self.start_netareamanager( netarea )

class Monitor_out(AMQPProducer,Thread):
	def __init__(self, ip, num_core, maxRam, maxNumNetareas, netarea_reports, Exit) :
		"""
			@param net_area id that descibe the partition of the net managed by this master
			@param in_tasks			incomming RecordTask type
		"""		
		Thread.__init__(self)
		AMQPProducer.__init__(self,"artemis_monitor_in")
		
		self.ip				= ip
		self.num_core		= num_core
		self.maxRam			= maxRam
		self.maxNumNetareas	= maxNumNetareas
		self.netarea_reports= netarea_reports
		self.Exit			= Exit
		
		logging.debug("Monitor_out initialized")

	def terminate(self):
		AMQPProducer.terminate(self)

	def run(self):
		logging.debug("Monitor_out started")
				
		while not self.Exit.is_set():
			print("report sent, ",len( self.netarea_reports) )
			report = MasterReport( self.ip, self.num_core, self.maxRam, self.maxNumNetareas, list(self.netarea_reports.values()) )
			self.add_task( serialize( report ) )
			sleep(1)
		
class NetareaManager(Process, AMQPProducer):
	"""
		Warning : One netareamanager by netarea on the whole network
	"""
	def __init__(self, net_area, in_workers, done_workers, out_workers, maxInTasksSize, maxDoneTasksSize, maxOutTasksSize, useragent, domainRules,
					protocolRules, originRules, delay, maxTasksMapSize, maxRobotsSize, netarea_report, order) :
		"""
			@param netarea			- netarea hash
			@param useragent		- 
			@param domainRules		- { "domain1" : bool (true ie allowed False forbiden) }, "*" is the default rule
			@param protocolRules	- { "protocol1" : bool (true ie allowed False forbiden) }, "*" is the default protocol
			@param originRules		- { "origin1" : bool (true ie allowed False forbiden) }, "*" is the default origin,
				the origin is the parent balise of the task
			@param delay			- period between two crawl of the same page
			@param maxRamSize		- maxsize of the tasks list kept in ram( in Bytes )
			@param numOverseer		- 
		"""
		Process.__init__(self)
		
		self.in_tasks			= LimitedDeque( maxInTasksSize )
		self.done_tasks			= LimitedDeque( maxDoneTasksSize )
		self.out_tasks			= LimitedDeque( maxOutTasksSize )
		
		self.report				= netarea_report
		self.order				= order
		
		self.Exit				= Event()
		self.InExit				= Event()
		self.ValidatorExit		= Event()
		self.DoneExit			= Event()
		self.OutExit			= Event()
		
		self.in_pool			= [ In_Worker(net_area, self.in_tasks, self.InExit ) for k in range(in_workers) ]	
		self.done_pool			= [ Done_Worker(net_area, self.done_tasks, self.DoneExit ) for k in range(done_workers) ]	
		self.validator			= Validator(useragent, delay,
											maxTasksMapSize, maxRobotsSize, self.in_tasks, self.done_tasks, self.out_tasks,
											self.report, self.order, self.ValidatorExit )	
		self.out_pool			= [ Out_Worker(self.out_tasks, self.OutExit ) for k in range(out_workers) ]
		
		logging.debug("NetareaManager started")

		
	def terminate(self):
		self.InExit.set()
		while self.in_pool :
			for w in self.in_pool:
				self.in_pool.remove( w ) if not w.is_alive() else ()
			sleep(0.1) if self.in_pool else () 
		
		self.DoneExit.set()
		while self.done_pool :
			for w in self.done_pool:
				self.done_pool.remove( w ) if not w.is_alive() else ()
			sleep(0.1) if self.done_pool else ()
		
		self.ValidatorExit.set()
		while self.validator and self.validator.is_alive():
			sleep(0.1)
		
		self.OutExit.set()
		while self.out_pool :
			for w in self.out_pool:
				self.out_pool.remove( w ) if not w.is_alive() else ()
			sleep(0.1) if self.out_pool else () 
			
		Process.terminate(self)
	
	def run(self):
		logging.debug("NetareaManager started")

		for w in self.in_pool:
			w.start()
		
		for w in self.done_pool:
			w.start()
		
		self.validator.start()
		
		for w in self.out_pool:
			w.start()
			
		while True:
			sleep(10)

class In_Worker(AMQPConsumer, Thread ):
	def __init__(self, net_area, in_tasks, Exit) :
		"""
			@param net_area id that descibe the partition of the net managed by this master
			@param in_tasks			incomming RecordTask type
		"""		
		Thread.__init__(self)
		
		AMQPConsumer.__init__(self, "artemis_master_in")
		self.channel.exchange_declare(exchange='artemis_master_in_direct', type='direct')
		self.channel.queue_declare(self.key, durable=False)
		self.channel.queue_bind(queue='artemis_master_in', exchange='artemis_master_in_direct', routing_key=str(net_area))
		
		self.net_area			= net_area
		self.in_tasks			= in_tasks
		self.Exit				= Exit
		
		logging.debug("In_Worker initialized")

		
	def run(self):
		logging.debug("In_Worker started")

		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while not self.Exit.is_set():
			self.channel.wait()
		
	def proccess(self, msg):
		print( "In tasks received", unserialize(msg.body))
		self.in_tasks.append( unserialize( msg.body ) )
		AMQPConsumer.process( self, msg)
	
class Done_Worker(AMQPConsumer, Thread ):
	def __init__(self, net_area, done_tasks, Exit) :
		"""
			@param net_area id that descibe the partition of the net managed by this master
			@param done_tasks			[ [task,tasks] ] incomming RecordTask type
		"""		
		Thread.__init__(self)
		
		AMQPConsumer.__init__(self, "artemis_master_done")
		self.channel.exchange_declare(exchange='artemis_master_done_direct', type='direct')
		self.channel.queue_declare(self.key, durable=False)
		self.channel.queue_bind(queue='artemis_master_done', exchange='artemis_master_done_direct', routing_key=str(net_area))
		
		self.net_area			= net_area
		self.done_tasks			= done_tasks
		self.Exit				= Exit
		
		logging.debug("Done_Worker initialized")

		
	def run(self):
		logging.debug("Done_Worker started")

		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while not self.Exit.is_set():
			self.channel.wait()
		
	def proccess(self, msg):
		print("Done task received", unserialize(msg.body) )
		self.done_tasks.append( unserialize( msg.body ) )
		AMQPConsumer.process( self, msg)
			
class Validator( Thread ):
	"""
		@brief One validator per Server
	"""
	def __init__(self, useragent, delay,
				maxTasksMapSize, maxRobotsSize, in_tasks, done_tasks, out_tasks, report, order, Exit) :
		"""
			@param useragent		- 
			@param period			- period between to wake up
			@param delay			- default period between two crawl of the same page
			@param maxRamSize		- maxsize of the tasks list kept in ram( in Bytes )
			@param in_tasks			- tasks incomming
			@param done_tasks		- tasks crawled
			@param out_tasks			processed tasks
		"""
		Thread.__init__(self)
		
		self.useragent 			= useragent
		self.delay				= delay # de maj
			
		self.maxTasksMapSize		= maxTasksMapSize
		self.maxRobotsSize		= maxRobotsSize
		
				
		self.tasksMap			= HybridDict( maxTasksMapSize, maxTasksMapSize * 20) 
		self.in_tasks			= in_tasks
		self.done_tasks			= done_tasks
		self.out_tasks			= out_tasks
		self.robotsMap			= RobotCacheHandler( maxRobotsSize, useragent=useragent )	
		
		self.report				= report
		self.order				= order
		self.Exit				= Exit
		
		logging.debug("Validator initialized")
		
	def is_valid(self, task):
		url = task.url
		if( url in self.tasksMap and  self.tasksMap[url].is_alive(self.delay) ):
			return False

		robot_url = ("https://" if task.scheme != "https" else "https://" ) +task.netloc+"/robots.txt"
		if robot_url not in self.robotsMap:
			sitemap = self.robotsMap.add(robot_url)
			if sitemap :
				self.in_tasks.append( Task(sitemap) )
			
		if not self.robotsMap[robot_url].can_fetch(task.url):
			return False

		if url in self.tasksMap : #merge
			task.lastvisited	= task.lastvisited if task.lastvisited != -1 else self.tasksMap[url].lastvisited
			task.lasthash		= task.lasthash if task.lasthash != "" else self.tasksMap[url].lasthash
			task.refreshrate	= task.refreshrate if task.refreshrate != 1 else self.tasksMap[url].refreshrate
			
		task.lastcontrolled = t_time()
		self.tasksMap[url]=task
		return True
	
	def validate(self):
		while self.in_tasks :
			task =  self.in_tasks.popleft()


			if self.is_valid( task ):
				print( task.url )
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
		for (key,task) in self.tasksMap.items() :
			if task.nature != TASK_WEB_STATIC_TORRENT and self.is_valid( task ):
				self.out_tasks.append( taskRecord )
			
	def run(self):
		logging.debug("Validator started")

		
		while not self.Exit.is_set():
			#if self.order.hight != -1 : je ne sais pas pk j'ai écrit ça...................
				#self.prune()
				
			self.refresh()
			self.validate()
			self.update()
			
			self.report.used_ram =  self.in_tasks.mem_length + self.done_tasks.mem_length
			self.report.used_ram += self.out_tasks.mem_length +self.robotsMap.mem_length
			self.report.used_ram += self.tasksMap.ram_length  
			sleep( 1 )
			
		#empty in_tasks
		self.refresh()
		self.validate()	

class Out_Worker( Thread ):
	def __init__(self, out_tasks, Exit) :
		"""
			@param out_tasks			
		"""		
		Thread.__init__(self)
		
		self.defaultProducer		= AMQPProducer("artemis_master_out")
		self.torrentProducer		= AMQPProducer("artemis_master_out_torrent")
		
		self.out_tasks			= out_tasks
		self.Exit				= Exit
		
		logging.debug("Out_Worker initialized")

		
	def add_tasks(self):
		while self.out_tasks:
			defautTasks = []
			torrents	= []

			try:
				for k in range( TASK_BUNDLE_LEN ) : 
					task = self.out_tasks.popleft()

					if task.nature == TASK_WEB_STATIC_TORRENT:
						torrents.append( task )
					else:
						defautTasks.append( task )
			except Exception :
				pass
				
			if defautTasks:
				self.defaultProducer.add_task( serialize(defautTasks) )
			if torrents:
				selt.torrentProducer.add_task( serialize(torrents) )

	def run(self):
		logging.debug("Out_Worker started")
	
		while not self.Exit.is_set():
			self.add_tasks()
			sleep(1)
		
		#empty out_tasks
		URL_BUNDLE_LEN=1
		self.add_tasks()
		
	
