from threading import Thread, RLock, Event
from multiprocessing import Process, Queue

from .Task import Task, TaskNature, AVERAGE_TASK_SIZE
from copy import copy, deepcopy
from .handlers.HandlerRules import getHandler
from .AVL import EmptyAVL

import mimetypes
import sys, traceback

import transmissionrpc 

import tempfile
import logging
from time import sleep, time
from .Netarea import Phi, NetareaTree #fonction utilisé pour associé une url à une netarea  url -> netarea key
from .Cache import  ARCCache
from collections import deque, defaultdict
import stem.process #tor
from stem.util import term
from .Utility import serialize, unserialize
from .accreditation.AccreditationCache import AccreditationCache
from .handlers.HTTPDefaultHandler import HTTPDefaultHandler
from .handlers.FTPDefaultHandler import FTPDefaultHandler
from .RessourceFactory	 import build

from .network.TcpServer import T_TcpServer, P_TcpServer, TcpServer
from .network.TcpClient import TcpClient
from .network.Msg		import MsgType, Msg
from .network.Reports	import SlaveReport, MonitorReport, SlaveMetrics


#logging.getLogger('transmissionrpc').setLevel(logging.DEBUG)

NUM_CLASS_TYPES 		= 6
RESSOURCE_BUNDLE_LEN 	= 10
SOCKS_PORT				= 7000 #tor

TASK_BUNDLE_LEN = 20 #task

#metric, local à un processus accessoirement
tasks_processed = 0
start_time = 0

mimetypes.init()

class VSlaveHearbeat( Thread ):
	def __init__(self, monitors, report, tasks, torrents, Exit, 
		monitors_lock):
		"""	
			@monitors
			@report and init report with constant, will be update durinf execution
			
		"""
		Thread.__init__(self)
		self.client 		= TcpClient()
		
		self.monitors		= monitors
		self.report			= report
		self.tasks			= tasks
		self.torrents		= torrents
		
		self.Exit 			= Exit
		self.monitors_lock	= monitors_lock
		
		logging.info("VSlaveHearbeat init")

	def update_report(self):
		self.report.used_ram = len(self.tasks)+len(self.torrents)
		self.report.used_ram *= AVERAGE_TASK_SIZE

	def run(self):
		while not self.Exit.is_set():
			self.update_report()
			
			with self.monitors_lock:
				for (host, port) in self.monitors:
					self.report.reset()
					
					self.client.send( 
						Msg(MsgType.ANNOUNCE_SLAVE , self.report), 
						host, port )
			sleep(1)
		
class Sender( Thread ): 
	def __init__(self, newTasks, doneTasks, netTree, domainRules,
		protocolRules, originRules, delay, Exit, netTree_lock):
		"""
			@param newTasks			- deque which contains the task collected by the crawlers
			@param netTree			- AVL which contains netaarea active on the network
			@param domainRules		- { "domain1" : bool (true ie allowed False forbiden) }, "*" is the default rule
			@param protocolRules	- { "protocol1" : bool (true ie allowed False forbiden) }, "*" is the default protocol
			@param originRules		- { "origin1" : bool (true ie allowed False forbiden) }, "*" is the default origin,
				the origin is the parent balise of the url
			@param delay			- default period between two crawl of the same page
			@param Exit 			- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief Send the collected urls to the master
		"""
		Thread.__init__(self)
		self.client 		= TcpClient()

		self.newTasks		= newTasks
		self.doneTasks		= doneTasks
		self.netTree		= netTree
		
		self.domainRules	= domainRules 
		self.protocolRules	= protocolRules
		self.originRules	= originRules
		
		self.delay			= delay
		self.alreadySent	= ARCCache( 10**4 ) 
		self.Exit			= Exit
		self.netTree_lock	= netTree_lock
		
		logging.info("Sender initialized")

	def is_valid(self, task):
		"""
			@brief			- it will chek 
				if the url match the domainRules, the protocolRules, the originRules,
				if the url is already in cache 
				if the url has been already visited during the "past delay"
				
		"""
		url = task.url
		
		if( url in  self.alreadySent
		and not self.alreadySent[url].is_expediable(self.delay) ):
			return False
		
		#if not self.originRules[task.origin]):
				#return False

		if not self.protocolRules[task.scheme] :
			  return False
		
		if not self.domainRules[task.netloc] :
			  return False
			  
		self.alreadySent[url]=task
		return True
		
		
	def process_list(self, tasks):
		buffers = defaultdict(list)

		while tasks:
			task 	= tasks.pop()
			with self.netTree_lock:
				key		= self.netTree.search( Phi(task) ).netarea
				host	= self.netTree[key].host
				port	= self.netTree[key].port
			
			buffers[key].append( task )
			
			if len( buffers[key] ) > TASK_BUNDLE_LEN :
				self.client.send(
					Msg(MsgType.MASTER_IN_TASKS, buffers[key]), 
					host, port)
				buffers[key] = []
		
		#empty the buffers
		for key in buffers:
			if buffers[key]: #len(buffers[key] <= TASK_BUNDLE_LEN
				with self.netTree_lock:
					host	= self.netTree[key].host
					port	= self.netTree[key].port
				self.client.send( 
					Msg(MsgType.MASTER_IN_TASKS, buffers[key]), 
					host, port)
				buffers[key] = []
				
	def process(self):
		new_tasks=[] #only valid and fresh urls
		
		while self.newTasks:
			task = self.newTasks.popleft()
			if self.is_valid( task ):
				new_tasks.append( task )
			
		self.process_list( new_tasks )
		self.process_list( self.doneTasks )
			 	
	def run(self):
		logging.info("Sender started")

		while not self.Exit.is_set():
			try:
				self.process()
			except EmptyAVL:
				pass
			sleep(1)
		
		self.process()
		logging.info("Sender stopped")
			
class CrawlerOverseer( Thread ):
	def __init__(self, useragent, maxCrawlers,  tasks, doneTasks, 
		newTasks, contentTypes, delay, ressources, Exit):
		"""
			@param useragent			- 
			@param maxCrawlers			- maximun number of crawlers
			@param tasks					- deque which contains the tasks received from the master
			@param contentTypes			- dict of allowed content type (in fact allowed rType cf.contentTypeRules.py)
			@param delay				- period between two crawl of the same page
			@param ressources	- ressources collected waiting for saving in sql( dict : [rType : deque of ressources,..]
			@param newTasks				- deque which contains the urls collected by the crawlers
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief Creates and monitors the crawlers
		"""
		Thread.__init__(self)
		self.useragent			= useragent
			
		self.maxCrawlers 		= maxCrawlers
		
		self.crawlers 			= []
		
		self.tasks				= tasks
		self.newTasks			= newTasks
		self.doneTasks			= doneTasks
		self.contentTypes		= contentTypes
		self.delay				= delay

		self.ressources			= ressources
		self.Exit				= Exit
		
		logging.info("CrawlerOverseer initialized")
		
	def terminate(self):		
		while len(self.crawlers)>0:
			for i in len(self.crawlers):
				if not self.crawlers[i].is_alive():
					del self.crawlers[i]
			
		logging.info("CrawlerOverseer stopped")
	
	def process(self):
		for i in range(self.maxCrawlers):
			w = Crawler( self.useragent, self.tasks, self.doneTasks, 
				self.newTasks, deepcopy(self.contentTypes), self.delay, 
				self.ressources, self.Exit )
			self.crawlers.append( w )
			w.start()
		
	def run(self):
		logging.info("CrawlerOverseer started")

		self.process()
		while not self.Exit.is_set(): # pas encore de role definit en attente despécification utltérieures
			sleep( 1 ) 
			
		self.terminate()
		
class Crawler( Thread ): 
	def __init__(self, useragent,  tasks, doneTasks, newTasks, 
		contentTypes, delay, ressources, Exit):
		"""
			@param tasks					- deque which contains the urls received from the master
			@param newTasks				- deque which contains the urls collected by the crawlers
			@param contentTypes			- dict of allowed content type (in fact allowed rType cf.contentTypeRules.py)
			@param delay				- period between two crawl of the same page
			@param ressources	- ressources collected waiting for saving in sql( dict : [rType : deque of ressources,..]
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief Will get ressources from the web, and will add data to waitingRessources and collected urls to newTasks
		"""
		Thread.__init__(self)
		self.useragent			= useragent
		
		self.tasks				= tasks
		self.newTasks			= newTasks
		self.doneTasks			= doneTasks
		self.contentTypes		= contentTypes 
		self.delay				= delay
				
		self.accreditationCache	= AccreditationCache(4194304, "/usr/local/conf/artemis/accreditation.sql") #4MB
			
		self.ressources			= ressources
		self.Exit 				= Exit
				
		self.contentTypesHeader = "*/*"
		if "*" in contentTypes and  (not self.contentTypes["*"]) :
			self.contentTypesHeader = ','.join([ 
				key 
				for key,flag in self.contentTypes.items() 
				if key != "*" and flag 
			])
		logging.info("Crawler initialized")

	def process(self):
		try:
			while True:	
				task = self.tasks.popleft() 
				self.dispatch( task )
		except Exception as e :
			logging.debug( "%s %s" % (
				traceback.extract_tb(sys.exc_info()[2]), str(e)))
			sleep(0.1)
	
	def run(self):
		logging.info("Crawler started")

		while not self.Exit.is_set():
			self.process()
			sleep(1)
		self.process()	
			
	def dispatch(self, task):
		"""
			@param url	-
			@brief selects the right function to  handle the protocl corresponding to the current url( http, ftp etc..)
		"""	
		if( task.nature == TaskNature.web_static 
		or task.nature == TaskNature.web_static_tor):
			if( task.scheme == "http" or task.scheme == "https"):
				self.http( task )
			elif( task.scheme == "ftp" or task.scheme == "ftps"):
				self.ftp( task )	
	
	def getTorProxies(self):
		return {
			"http": "sock5://127.0.0.1:"+str(SOCKS_PORT)+"/", 
			"https": "sock5://127.0.0.1:"+str(SOCKS_PORT)+"/"
		}
	
	def ftp(self, task):
		handler = getHandler( task )( self.accreditationCache )
		newTasks, tmpFile = handler.execute( task )
		
		if task.is_dir:
			contentType, encoding = "inode/directory", None
		else:
			contentType, encoding = mimetypes.guess_type(task.url, 
				strict=False) #encoding often None
		
		ressource, tasks		= build(
			tmpFile, 
			task, 
			contentType if contentType else "application/octet-stream", 
			self.contentTypes, 
			self.useragent)

		if ressource :  
			self.newTasks.extend( tasks )
			self.ressources.append( ressource )
			
		task.lastvisited 	= time()
		task.lastcontrolled	= task.lastvisited
		
		self.newTasks.extend( newTasks )
		self.doneTasks.append( task )
				
	def http( self, task ): 
		"""
			@param task		-	
			@param urlObj	- ParseResult (see urllib.parse), which represents the current url
			@brief connects to  the remote ressource and get it
		"""
		#proxies = (self.getTorProxies() if task.nature	== TASK_WEB_STATIC_TOR else None), not until requests support sock5
		proxies=None
		
		handler = getHandler(task)( self.useragent, 
			self.contentTypesHeader, self.accreditationCache, 
			proxies, SOCKS_PORT)
		
		contentType, tmpFile, redirectionTasks = handler.execute( task )
		
		ressource, tasks	= build(tmpFile,
			task, 
			contentType, 
			self.contentTypes, 
			self.useragent)

		if ressource :  
			self.newTasks.extend( tasks )
			self.ressources.append( ressource )
		
		task.lastvisited 	= time()
		task.lastcontrolled	= task.lastvisited
		self.doneTasks.append( task )
		self.newTasks.extend( redirectionTasks )
	
class TorrentHandler( Thread ):
	def __init__(self, torrents, contentTypes, maxActiveTorrents, 
		useragent, doneTasks, newTasks, ressources, Exit):
		"""
			@param urls					- deque which contains the urls received from the master
			@param newTasks				- deque which contains the urls collected by the crawlers
			@param ressources	- ressources collected waiting for saving in sql( dict : [rType : deque of ressources,..]
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief A torrent must not be recrawl ?
		"""
		Thread.__init__(self)
		
		self.torrents			= torrents
		self.maxActiveTorrents	= maxActiveTorrents
		self.contentTypes		= contentTypes 
		self.useragent			= useragent
		
		self.doneTasks			= doneTasks
		self.newTasks			= newTasks			
		self.ressources			= ressources
		self.Exit 				= Exit
		
		self.client = transmissionrpc.Client('localhost', port=9091)
		
		self.activeTorrents = {}
		logging.info("TorrentHandler initialized")
	
	def add_torrent(self, task):
		try:
			tmpDir = tempfile.TemporaryDirectory()
			torrent_id = (self.client.add_torrent(task.url, download_dir=tmpDir.name)).id
			self.activeTorrents[torrent_id] = ( (task, tmpDir) )
		except Exception as e:
			logging.debug( "%s %s %s" % (
				traceback.extract_tb(sys.exc_info()[2]), str(e), str(task)))
			pass

		
	def run(self):
		while not self.Exit.is_set():
			for torrent_id, (task,  tmpDir) in list(self.activeTorrents.items()):
				try:
					torrent = self.client.get_torrent( torrent_id ) 
				except Exception as e:
					task.lastvisited 	= time()
					task.lastcontrolled	= task.lastvisited
					
					self.doneTasks.append( task )
					
					self.client.stop_torrent( torrent_id )
					self.client.remove_torrent( torrent_id )
					del self.activeTorrents[torrent_id]
						
					logging.debug( "%s %s %s" % (
						traceback.extract_tb(sys.exc_info()[2]), 
						str(e), str(task)))
					
				if torrent.progress == 100: #ie download finished
					task.lastvisited 	= time()
					task.lastcontrolled	= task.lastvisited
					ressource, tasks = build(tmpDir,
						task,
						"inode/directory", 
						self.contentTypes, 
						task.url
					)
					
					if ressource :
						self.newTasks.extend( tasks )
						self.ressources.append( ressource )						
					self.doneTasks.append( task )
					
					self.client.stop_torrent( torrent_id )
					self.client.remove_torrent( torrent_id )
					del self.activeTorrents[torrent_id]					
					
				elif torrent.status == "stopped":
					task.lastvisited 	= time()
					task.lastcontrolled	= task.lastvisited
					
					self.doneTasks.append( task )
					
					self.client.stop_torrent( torrent_id )
					self.client.remove_torrent( torrent_id )
					del self.activeTorrents[torrent_id]
		
					logging.debug("torrent failed %s" % task)
									
			while( len(self.activeTorrents) < self.maxActiveTorrents 
			and  self.torrents):
				self.add_torrent( self.torrents.popleft() )
			sleep(1)

class WorkerOverseer(Thread):
	def __init__(self, maxWorkers, dfs_path, ressources, savedRessources,
		Exit):
		"""
			@param maxWorkers			- maximun number of workers handled by this overseer
			@param ressources			- coming from crawler
			@param savedRessources		- ressources saved in DFS
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
		"""
		Thread.__init__(self)

		self.ressources			= ressources
		self.savedRessources	= savedRessources
		self.maxWorkers			= maxWorkers
		self.dfs_path			= dfs_path
		self.Exit 				= Exit
		
		self.workers			= []
		
		logging.info("WorkerOverseer initialized")


	def terminate(self):
		while len(self.workers)>0:
			for i in len(self.workers):
				if not self.workers[i].is_alive():
					del self.workers[i]
			sleep(0.1)
		
		logging.info( "WorkerOverseer end")
		
	def process(self):
		for i in range(self.maxWorkers):
			w = Worker( self.dfs_path, self.ressources, 
				self.savedRessources, self.Exit )
			self.workers.append( w )
			w.start()
	
	def run(self):
		logging.info("WorkerOverseer started")

		self.process()
		while not self.Exit.is_set(): # pas encore de role definit en attente despécification utltérieures
			sleep( 1 ) 
		
		self.terminate()
		
class Worker(Thread):
	"""
		@brief saves a ressource on DFS
	"""
	def __init__(self, dfs_path, ressources, savedRessources,  Exit):
		Thread.__init__(self)
		
		self.dfs_path			= dfs_path
		self.ressources			= ressources
		self.savedRessources	= savedRessources
		self.Exit 				= Exit
		
		logging.info("Worker initialized")

		
	def process(self):
		try:
			while self.ressources:
				ressource = self.ressources.popleft()
				ressource.save( self.dfs_path )
				
				self.savedRessources.extend( ressource.rec_children() ) 
				self.savedRessources.append( ressource )

				global tasks_processed
				tasks_processed += 1
		except Exception as e:
			logging.debug( "%s %s %s" % (
				traceback.extract_tb(sys.exc_info()[2]), str(e),
				str(ressource) ))
			pass
	
	def run(self):		
		while not self.Exit.is_set():
			self.process()
			sleep(1)
			
		self.process()
		
class Out_Interface( Thread ):
	def __init__(self, savedRessources, Exit) :
		Thread.__init__(self)
		#not implented how and where the msg will be sent
		#self.client	= TcpClient()
		logging.warning("No out interface yet")
		
		self.savedRessources	= savedRessources
		self.Exit				= Exit
		
		logging.info("Out_Interface initialized")
		
	def send(self):
		while self.savedRessources:  
			ressources = []
			try:
				for k in range( RESSOURCE_BUNDLE_LEN ) : 
					ressouce = self.savedRessources.popleft() 
					ressources.append( ressource._id )
			except Exception :
				pass
			
			if ressources:
				ressources=[]
				#self.client.send( Msg( something ,ressources), somewhere, somewhere )
				
	def run(self):
		logging.info("Out_Interface started")
			
		while not self.Exit.is_set():
			self.send()
			sleep(1)
		
		RESSOURCE_BUNDLE_LEN = 1
		self.add_tasks()

class VSlave(P_TcpServer):
	def __init__(self, host, monitors, useragent, maxCrawlers, maxWorkers, 
		delay, dfs_path, contentTypes, domainRules, 
		protocolRules, originRules, maxTasks, maxTorrents, 
		maxNewTasks, maxDoneTasks, maxRessources, 
		maxSavedRessources, maxActiveTorrents) :
		"""
			@param useragent		- 
			@param period			- period between to wake up
			@param maxWorkers		- maximun number of workers handled by an instance of WorkerOverseer
			@param contentTypes		- dict of allowed content type (in fact allowed rType cf.contentTypeRules.py)
			@param delay			- period between two crawl of the same page
			@param maxCrawlers		- maximun number of crawlers handled by an instance of CrawlerOverseer
			@param sqlNumber		-
			@brief
		"""
		P_TcpServer.__init__(self, host)
		self.host = self.get_host()
		
		self.monitors			= monitors
		self.useragent			= useragent
		
		self.maxCrawlers		= maxCrawlers
		self.maxWorkers 		= maxWorkers
		
		self.delay				= delay
		self.dfs_path			= dfs_path
		
		self.netTree			= NetareaTree()
		self.contentTypes		= contentTypes
		self.domainRules		= domainRules
		self.protocolRules		= protocolRules
		self.originRules		= originRules
		
		self.maxActiveTorrents	= maxActiveTorrents
		
		self.maxTasks		= maxTasks
		self.maxTorrents	= maxTorrents
		
		
		self.tasks				= deque( maxlen=maxTasks )
		self.torrents			= deque( maxlen=maxTorrents )
		self.maxTasks			= int(maxTasks / 2048) # assuming that an url len is less than 2048
		self.maxTorrents		= int(maxTasks / 4096) # assuming that an url len is less than 2048
		self.newTasks			= deque( maxlen=maxNewTasks )
		self.doneTasks			= deque( maxlen=maxDoneTasks )
		self.ressources			= deque( maxlen=maxRessources )
		self.savedRessources	= deque( maxlen=maxSavedRessources )
	
		

		self.VSlaveHearbeat_Exit 			= Event()
		self.In_Torrent_Interface_Exit 		= Event()
		self.Sender_Exit 					= Event()
		self.CrawlerOverseer_Exit 			= Event()
		self.TorrentHandler_Exit 			= Event()
		self.WorkerOverseer_Exit 			= Event()
		self.Out_Interface_Exit				= Event()
		
		self.monitors_lock					= RLock()
		self.netTree_lock					= RLock()
		
		self.running		= False # True when netTree received
		
		self.vSlaveHeartbeat	= VSlaveHearbeat( self.monitors, 
			SlaveReport(self.get_host(), self.port, 0, 
				self.maxTasks+self.maxTorrents),
			self.tasks, self.torrents, self.VSlaveHearbeat_Exit, 
				self.monitors_lock )
		self.vSlaveHeartbeat.start()

		logging.info("Server initialized")

	def stop_sender(self):
		self.Sender_Exit.set()
		while self.sender.is_alive():
			sleep(1)
			
	def start_sender(self):
		self.sender	= Sender( self.newTasks, 
			self.doneTasks, 
			self.netTree, 
			self.domainRules, 
			self.protocolRules, 
			self.originRules, 
			self.delay, 
			self.Sender_Exit,
			self.netTree_lock)
			
		self.Sender_Exit.clear()
		self.sender.start()
		
	def terminate(self):
		self.VSlaveHearbeat_Exit.set()
		while self.vSlaveHeartbeat.is_alive():
			sleep(2)
		
		self.CrawlerOverseer_Exit.set()
		while self.crawlerOverseer.is_alive():
			sleep(1)
			
		self.TorrentHandler_Exit.set()
		while self.torrentHandler.is_alive():
			sleep(1)
		
		self.stop_sender()
			
		self.WorkerOverseer_Exit.set()
		while self.workerOverseer.is_alive():
			sleep(1)
		
		self.Out_Interface_Exit.set()
		while self.outInterface.is_alive():
			sleep(1)
			
		Process.terminate(self)
	
	def harness(self):
		#We only need to know the in memory limitation
		self.crawlerOverseer= CrawlerOverseer( self.useragent, 
			self.maxCrawlers,  self.tasks, self.doneTasks, self.newTasks,
			self.contentTypes, self.delay, self.ressources, 
			self.CrawlerOverseer_Exit)
		self.torrentHandler	= TorrentHandler( self.torrents, 
			self.contentTypes, self.maxActiveTorrents, self.useragent, 
			self.doneTasks, self.newTasks, self.ressources, 
			self.TorrentHandler_Exit)
		self.workerOverseer	= WorkerOverseer( self.maxWorkers, 
			self.dfs_path, self.ressources, self.savedRessources,  
			self.WorkerOverseer_Exit)				
		self.outInterface	= Out_Interface( self.savedRessources, 
			self.Out_Interface_Exit) 
		
		start_time	= time()
		
		self.start_sender()
		self.crawlerOverseer.start()
		self.torrentHandler.start()
		self.workerOverseer.start()
		self.outInterface.start()	
		
		self.client 		= TcpClient()
		
	def callback(self, data):
		msg	= TcpServer.callback(self, data)
		if msg.t == MsgType.SLAVE_IN_TASKS :
			for task in msg.obj:
				if( task.nature == TaskNature.web_static_torrent ):
					self.torrents.append( task )
				else:
					self.tasks.append( task )
		elif( msg.t == MsgType.ANNOUNCE_NET_TREE_UPDATE_INCOMING 
		and self.running):
			self.stop_sender()
		elif( msg.t == MsgType.ANNOUNCE_NET_TREE_PROPAGATE 
		and self.running):
			with self.netTree_lock:
				for net in msg.obj[1]:
					self.netTree.suppr( net.netarea )

				for net in msg.obj[0]:
					self.netTree[ net.netarea] = net
					
				for net in msg.obj[2]:
					self.netTree[ net.netarea ].next_netarea= net.next_netarea
					self.netTree[ net.netarea ].used_ram 	= net.used_ram 
			self.start_sender()	
		elif( msg.t == MsgType.ANNOUNCE_NET_TREE and not msg.obj.empty() 
		and not self.running):
			with self.netTree_lock:
				self.netTree.update( msg.obj  )
			self.harness()
			self.running= True
		elif(msg.t == MsgType.ANNOUNCE_NET_TREE_PROPAGATE and not self.running ):
			with self.netTree_lock:
				for net in msg.obj[1]:
					self.netTree.suppr( net.netarea )
				
				for net in msg.obj[0]:
					self.netTree[ net.netarea] = net
					
				for net in msg.obj[2]:
					self.netTree[ net.netarea ].next_netarea= net.next_netarea
					self.netTree[ net.netarea ].used_ram 	= net.used_ram 
			
				if not self.netTree.empty():
					self.harness()
					self.running= True
		elif msg.t == MsgType.ANNOUNCE_MONITORS:
			with self.monitors_lock:
				self.monitors.clear()
				self.monitors.update( msg.obj )
		elif msg.t == MsgType.metric_expected:
			host, port = msg.obj
			global tasks_processed, start_time

			self.client.send( Msg( MsgType.metric_slave, SlaveMetrics( 
				self.get_host(), self.port, 
				tasks_processed, time() - start_time) ), host, port )

			tasks_processed = 0
			start_time 		= time()
		else:
			logging.info("Unknow received msg %s" % msg.pretty_str())
			
class Slave:
	def __init__(self, host, monitors, serverNumber, useragent, maxCrawlers, 
		maxWorkers, delay, dfs_path, contentTypes, 
		domainRules, protocolRules, originRules, maxTasks, 
		maxTorrents, maxNewTasks, maxDoneTasks,
		maxRessources, maxSavedRessources, maxActiveTorrents):
		
		self.pool			= []
		self.serverNumber 	= serverNumber
		
		for i in range(self.serverNumber):
			s = VSlave(host, monitors, useragent, maxCrawlers, maxWorkers, 
				delay, dfs_path, contentTypes, domainRules, 
				protocolRules, originRules, maxTasks, 
				maxTorrents, maxNewTasks, maxDoneTasks,
				maxRessources, maxSavedRessources, 
				maxActiveTorrents)
			self.pool.append( s )
		
		self.initTor()
		
		logging.info("Slave initialized")

	def initTor(self):
		return None;
		self.tor_process = stem.process.launch_tor_with_config(
		#tor_cmd="extras/Tor/tor",
		config = {'SocksPort': str(SOCKS_PORT)},
		init_msg_handler = lambda line : logging.info( 
			term.format(line, term.Color.BLUE) )
		)

	def terminate(self):
		for server in self.pool:
			server.terminate() if server.is_alive() else () 
		
		self.tor_process.kill()
		
		logging.info("Servers stoped")

	def harness(self):
		logging.info("Slave started")

		for s in self.pool:
			s.start()
			
		while True:
			sleep(10)
