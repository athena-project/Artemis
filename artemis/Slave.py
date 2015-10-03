import copy
import shutil

from email.utils import formatdate

import time
import hashlib

from collections import deque
from threading import Thread, RLock, Event
from multiprocessing import Process, Queue

from .Task import TASK_WEB_STATIC_TORRENT, TASK_WEB_STATIC, TASK_WEB_STATIC_TOR, Task
from copy import copy, deepcopy
from .handlers.HandlerRules import HandlerRules

import mimetypes

from .network.AMQPConsumer import AMQPConsumer
from .network.AMQPProducer import AMQPProducer

import transmissionrpc 

import tempfile
import logging
from time import sleep
from .Netarea import Phi, NetareaTree #fonction utilisé pour associé une url à une netarea  url -> netarea key
from .LimitedCollections import LimitedDeque, LimitedDict
import stem.process #tor
from stem.util import term
import artemis.db.SQLFactory as SQLFactory
from .Utility import serialize, unserialize
from .Forms import SQLFormManager, Form
from .accreditation.AccreditationCacheHandler import AccreditationCacheHandler
from .handlers.HTTPDefaultHandler import HTTPDefaultHandler
from .handlers.FTPDefaultHandler import FTPDefaultHandler
from .RessourceFactory	 import RessourceFactory
from .Monitor import HEADER_SENDER_STOP, HEADER_SENDER_START, HEADER_SENDER_DEFAULT
import artemis.pyHermes as pyHermes



NUM_CLASS_TYPES = 6
RESSOURCE_BUNDLE_LEN = 10
SOCKS_PORT			= 7000 #tor

TASK_BUNDLE_LEN = 10 #task


mimetypes.init()

class In_Interface(AMQPConsumer, Thread ):
	def __init__(self, tasks, maxTasks, Exit) :
		"""
			@param tasks			incomming Task type
			@param maxTasks		describe the number of tasks in the  buffer
		"""		
		Thread.__init__(self)
		AMQPConsumer.__init__(self, "artemis_master_out")
		
		self.maxTasks		= maxTasks
		self.tasks			= tasks
		self.Exit			= Exit
		
		logging.info("In_Interface initialized")
		
	def run(self): 
		logging.info("In_Interface started")
		self.consume()
		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while not self.Exit.is_set():
			while len(self.tasks)<self.maxTasks :
				self.channel.wait()
			sleep(1)
		
	def proccess(self, msg):
		#print( "Tasks received",len( unserialize(msg.body) ))
		self.tasks.extend( unserialize( msg.body ) )
		AMQPConsumer.process( self, msg)
		
class In_Torrent_Interface(AMQPConsumer, Thread ):
	def __init__(self, torrents, maxTorrents, Exit) :
		"""
			@param torrents			incomming Torrents 
			@param maxTorrents		describe the number of torrents in the  buffer
		"""		
		Thread.__init__(self)
		AMQPConsumer.__init__(self, "artemis_master_out_torrent")
		
		self.maxTorrents	= maxTorrents
		self.torrents		= torrents
		self.Exit			= Exit
		
		logging.info("In_Torrent_Interface initialized")
	def run(self):
		logging.info("In_Torrent_Interface started")

		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while not self.Exit.is_set():
			while len(self.torrents)<self.maxTorrents :
				self.channel.wait()
			sleep(1)
		
	def proccess(self, msg):
		#print( "Torrents received",len( unserialize(msg.body) ))

		self.torrents.extend( unserialize( msg.body ) )
		AMQPConsumer.process( self, msg)
			
class Sender( Thread ): 
	def __init__(self, newTasks, doneTasks, netTree, domainRules, protocolRules, originRules, delay, Exit):
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
		self.new_producer			= AMQPProducer("artemis_master_in")
		self.new_producer.channel.exchange_declare(exchange='artemis_master_in_direct', type='direct')
		self.new_producer.channel.queue_declare("artemis_master_in", durable=False)

		self.done_producer			= AMQPProducer("artemis_master_done")
		self.done_producer.channel.exchange_declare(exchange='artemis_master_done_direct', type='direct')
		self.done_producer.channel.queue_declare("artemis_master_done", durable=False)

		self.newTasks		= newTasks
		self.doneTasks		= doneTasks
		self.netTree		= netTree
		
		self.domainRules	= domainRules 
		self.protocolRules	= protocolRules
		self.originRules	= originRules
		
		self.delay			= delay
		self.alreadySent	= LimitedDict( 1<<22 ) #voir la taille
		self.Exit			= Exit
		
		logging.info("Sender initialized")

	
	def is_valid(self, task):
		"""
			@brief			- it will chek 
				if the url match the domainRules, the protocolRules, the originRules,
				if the url is already in cache 
				if the url has been already visited during the "past delay"
				
		"""
		url = task.url
		if( url in self.alreadySent and  not self.alreadySent[url].is_expediable(self.delay) ):
			return False
		
		#if  (task.origin not in self.originRules and not self.originRules["*"])  or  (task.origin in self.originRules and not self.originRules[task.origin]):
				#return False

		if (task.scheme not in self.protocolRules and not self.protocolRules["*"]) or  (task.scheme in self.protocolRules and not self.protocolRules[task.scheme]):
			  return False
		
		if (task.netloc not in self.domainRules and not self.domainRules["*"])  or  (task.netloc in self.domainRules and not self.domainRules[task.netloc]):
			  return False
			  
		self.alreadySent[url]=task
		return True
		
	def process(self):
		new_tasks=[] #only valid and fresh urls
		
		while self.newTasks:
			task = self.newTasks.popleft()
			if self.is_valid( task ):
				new_tasks.append( task )
		
		buffers={}
		while new_tasks:
			task 	= new_tasks.pop()
			key	= self.netTree.search( Phi(task) ).netarea
			if key not in buffers:
				buffers[key]=[]
			
			buffers[key].append( task )
			
			if len( buffers[key] ) > TASK_BUNDLE_LEN :
				self.new_producer.add_task( serialize( buffers[key] ), exchange="artemis_master_in_direct", routing_key=str(key)  )
				buffers[key] = []
		
		#empty the buffers
		for key in buffers:
			if buffers[key]: #len(buffers[key] <= TASK_BUNDLE_LEN
				self.new_producer.add_task( serialize( buffers[key] ), exchange="artemis_master_in_direct", routing_key=str(key)  )
				buffers[key] = []
				
		buffers={}		
		while self.doneTasks :
			task = self.doneTasks.popleft()
			key	= self.netTree.search( Phi(task) ).netarea
			if key not in buffers:
				buffers[key]=[]
			
			buffers[key].append( task )
			
			if len( buffers[key] ) > TASK_BUNDLE_LEN :
				self.new_producer.add_task( serialize(buffers[key]), exchange="artemis_master_done_direct", routing_key=str(key)  )
				buffers[key]={}
		
		#empty the buffers
		for key in buffers:
			if buffers[key]: #len(buffers[key] <= TASK_BUNDLE_LEN
				self.new_producer.add_task( serialize( buffers[key] ), exchange="artemis_master_done_direct", routing_key=str(key)  )
				buffers[key] = []
			 	
	def run(self):
		logging.info("Sender started")

		while not self.Exit.is_set():
			self.process()
			time.sleep(1)
		
		self.process()
		logging.info("Sender stopped")
			
class CrawlerOverseer( Thread ):
	def __init__(self, useragent, maxCrawlers,  tasks, doneTasks, newTasks, newForms, contentTypes, delay, unorderedRessource, Exit):
		"""
			@param useragent			- 
			@param maxCrawlers			- maximun number of crawlers
			@param tasks					- deque which contains the tasks received from the master
			@param contentTypes			- dict of allowed content type (in fact allowed rType cf.contentTypeRules.py)
			@param delay				- period between two crawl of the same page
			@param unorderedRessource	- ressources collected waiting for saving in sql( dict : [rType : deque of ressources,..]
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
		self.newForms			= newForms
		self.doneTasks			= doneTasks
		self.contentTypes		= contentTypes
		self.delay				= delay

		self.unorderedRessource	= unorderedRessource
		self.Exit				= Exit
		
		#self.initTor()
		
		logging.info("CrawlerOverseer initialized")
		
	def initTor(self):
		
		self.tor_process = stem.process.launch_tor_with_config(
		#tor_cmd="extras/Tor/tor",
		config = {'SocksPort': str(SOCKS_PORT)},
		init_msg_handler = lambda line : logging.info( term.format(line, term.Color.BLUE) )
		)
	
	def terminate(self):		
		while len(self.crawlers)>0:
			for i in len(self.crawlers):
				if not self.crawlers[i].is_alive():
					del self.crawlers[i]
		sleep(0.1)
			
		self.tor_process.kill()
		logging.info("CrawlerOverseer stopped")
	
	def process(self):
		for i in range(self.maxCrawlers):
			w = Crawler( self.useragent, self.tasks, self.doneTasks, self.newTasks, self.newForms,
				deepcopy(self.contentTypes), self.delay, self.unorderedRessource, self.Exit )
			self.crawlers.append( w )
			w.start()
		
	def run(self):
		logging.info("CrawlerOverseer started")

		self.process()
		while not self.Exit.is_set(): # pas encore de role definit en attente despécification utltérieures
			time.sleep( 1 ) 
			
		self.terminate()
		
class Crawler( Thread ): 
	def __init__(self, useragent,  tasks, doneTasks, newTasks, newForms, contentTypes, delay, unorderedRessources, Exit):
		"""
			@param tasks					- deque which contains the urls received from the master
			@param newTasks				- deque which contains the urls collected by the crawlers
			@param contentTypes			- dict of allowed content type (in fact allowed rType cf.contentTypeRules.py)
			@param delay				- period between two crawl of the same page
			@param unorderedRessource	- ressources collected waiting for saving in sql( dict : [rType : deque of ressources,..]
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief Will get ressources from the web, and will add data to waitingRessources and collected urls to newTasks
		"""
		Thread.__init__(self)
		self.useragent			= useragent
		
		self.tasks				= tasks
		self.newTasks			= newTasks
		self.newForms			= newForms
		self.doneTasks			= doneTasks
		self.contentTypes		= contentTypes 
		self.delay				= delay
				
		self.handlerRules		= copy( HandlerRules )
		self.accreditationCacheHandler	= AccreditationCacheHandler(4194304) #4MB
			
		self.unorderedRessources= unorderedRessources
		self.Exit 				= Exit
				
		self.contentTypesHeader = "*/*;"
		if "*" in contentTypes and  (not self.contentTypes["*"]) :
			self.contentTypesHeader =""
			for key,flag in self.contentTypes.items():
				if key != "*" and flag:
					self.contentTypesHeader+=key+"; ,"
		
		logging.info("Crawler initialized")

		
	def process(self):
		try:
			while True:	
				task = self.tasks.popleft()
				#print("Crawler : ", task.url)
				self.dispatch( task )
		except Exception as e:
			print(e)
			logging.debug( e )
	
	def run(self):
		logging.info("Crawler started")

		while not self.Exit.is_set():
			self.process()
			time.sleep(1)
		self.process()	
			
	def dispatch(self, task):
		"""
			@param url	-
			@brief selects the right function to  handle the protocl corresponding to the current url( http, ftp etc..)
		"""
		#print(task.url)
		if task.nature == TASK_WEB_STATIC or  task.nature == TASK_WEB_STATIC_TOR:
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
		print("ftp : ", task.url, "  nature = ",task.nature)

		if task.netloc not in self.handlerRules["ftp"]:
			handler = FTPDefaultHandler( self.accreditationCacheHandler)
		else:
			handler = self.handlerRules["ftp"][ task.netloc ]( self.accreditationCacheHandler)#ftp/ftps -> same 
		
		newTasks, tmpFile = handler.execute( task )
		
		if task.is_dir:
			contentType, encoding = "inode/directory", None
		else:
			contentType, encoding = mimetypes.guess_type(task.url, strict=False) #encoding often None
		#print("contentType ",contentType)	
		ressource, tasks, forms, children	= RessourceFactory.build(tmpFile, task, contentType, self.contentTypes, self.useragent)
		if ressource :  
			self.newTasks.extend( tasks )
			self.newForms.extend( forms )
			self.unorderedRessources[ ressource.getClass_type() ].append( (task, ressource, tmpFile) )
			
			for key, r in children.items():
				self.unorderedRessources[ key ].append( r )
			
		task.lastvisited 	= time.time()
		task.lastcontrolled	= task.lastvisited
		#print( newTasks)
		self.newTasks.extend( newTasks )
		self.doneTasks.append( task )
		
	def http( self, task ): 
		"""
			@param task		-	
			@param urlObj	- ParseResult (see urllib.parse), which represents the current url
			@brief connects to  the remote ressource and get it
		"""
		#print("http : ", task.url, "  nature = ",task.nature)
		#proxies = (self.getTorProxies() if task.nature	== TASK_WEB_STATIC_TOR else None), not until requests support sock5
		proxies=None
		
		if task.netloc not in self.handlerRules["http"]:
			handler = HTTPDefaultHandler(self.useragent, self.contentTypesHeader, self.accreditationCacheHandler, proxies, SOCKS_PORT)
		else:
			handler = self.handlerRules["http"][ task.netloc ](self.useragent, self.contentTypesHeader, self.accreditationCacheHandler, proxies, SOCKS_PORT)#http/https -> same 
		
		contentType, tmpFile, redirectionTasks = handler.execute( task )
		
		ressource, tasks, forms, children	= RessourceFactory.build(tmpFile, task, contentType, self.contentTypes, self.useragent)

		if ressource :  
			#print("tasks", len(tasks))
			#print("pre-forms: ", len(forms))
			self.newTasks.extend( tasks )
			self.newForms.extend( forms )
			self.unorderedRessources[ ressource.getClass_type() ].append( (task, ressource, tmpFile) )
			
			for key, r in children.items():
				self.unorderedRessources[ key ].append( r )
		
		task.lastvisited 	= time.time()
		task.lastcontrolled	= task.lastvisited
		self.doneTasks.append( task )
		self.newTasks.extend( redirectionTasks )
		
class TorrentHandler( Thread ):
	def __init__(self, torrents, contentTypes, maxActiveTorrents, useragent, doneTasks, newTasks, unorderedRessource, Exit):
		"""
			@param urls					- deque which contains the urls received from the master
			@param newTasks				- deque which contains the urls collected by the crawlers
			@param unorderedRessource	- ressources collected waiting for saving in sql( dict : [rType : deque of ressources,..]
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
		self.unorderedRessource	= unorderedRessource
		self.Exit 				= Exit
		
		self.client = transmissionrpc.Client('localhost', port=9091)
		
		self.activeTorrents = []
		logging.info("TorrentHandler initialized")
	
	def add_torrent(self, task):
		tmpDir = tempfile.TemporaryDirectory()
		torrent_id = (self.client.add_torrent(task.url, download_dir=tmpDir.name)).id
		print("Adding torrent", task.url)
		print("Torrent_id", torrent_id)
		self.activeTorrents.append( (task, torrent_id, tmpDir) )
		
	def run(self):
		logging.info("TorrentHandler started")

		while not self.Exit.is_set():
			for (task, torrent_id, tmpDir) in self.activeTorrents:
				torrent = self.client.get_torrent( torrent_id ) 
				
				print("Torrent active, ", task.url)
				print("name: ", torrent.name, "  status: ", torrent.status, "  progress: ", torrent.progress)
					
				if torrent.progress == 100: #ie download finished
					task.lastvisited 	= time.time()
					task.lastcontrolled	= task.lastvisited
					
					ressource, tasks, forms, children			= RessourceFactory.build(tmpDir, task, "inode/directory", self.contentTypes, "torrent:"+self.useragent)
					
					if ressource :
						self.newTasks.extend( tasks )
						self.unorderedRessource[ pyHermes.t_Directory ].appendleft( (task, ressource, tmpDir) )
						
						for key, r in children.items():
							self.unorderedRessources[ key ].append( r )
						
					self.doneTasks.append( task )
					
					self.client.stop_torrent( torrent_id )
					self.client.remove_torrent( torrent_id )
					self.activeTorrents.remove( (task, torrent_id, tmpDir) ) 
				
				if torrent.status == "stopped":
					task.lastvisited 	= time.time()
					task.lastcontrolled	= task.lastvisited
					
					self.doneTasks.append( task )
					
					self.client.stop_torrent( torrent_id )
					self.client.remove_torrent( torrent_id )
					self.activeTorrents.remove( (task, torrent_id, tmpDir) ) 
					
			while len(self.activeTorrents) < self.maxActiveTorrents and  self.torrents:
				self.add_torrent( self.torrents.popleft() )
			sleep(1)
			
class SQLHandler( Thread ):							
	def __init__(self,  number, unorderedRessources, orderedRessources, newForms, Exit):	
		"""
			@param number				- insert and update pool size
			@param unorderedRessources	- ressources collected waiting for saving in sql( dict : [rType : deque of ressources,..]
			@param orderedRessources	- after saved in db
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
			@brief handle sql requests, inserts newly collected ressources, and updates analysed ones
		"""
		
		Thread.__init__(self); 
		self.managers 			= {}
		self.number				= number
		self.unorderedRessources= unorderedRessources
		self.orderedRessources	= orderedRessources
		self.newForms			= newForms
		self.Exit				= Exit

		self.manager			= pyHermes.SQLRessourceManager()
		self.formManager		= SQLFormManager( SQLFactory.getConn() )
		
		logging.info("SQLHandler initialized")
					
	def process(self):
		for class_type in self.unorderedRessources:
			while len( self.unorderedRessources[class_type])>self.number :
				ressources 	= []
				tmpfiles	= []
				tasks 		= []

				for k in range(self.number):
					task, ressource, tmpFile = self.unorderedRessources[class_type].popleft()
					ressources.append( ressource )
					self.manager.add_acc(ressource)
					tmpfiles.append( tmpFile )
				#for r in ressources:
					#print( r.getMetadata().get("contentType"), "       ",  r.getClass_type())
					#print(len(ressources))
				
				i=self.manager.insert_with_acc(class_type)
				n=len(ressources)
				for k in range(n):
					ressources[k].setId(i-n+k+1)
				#print("End, insertion", i) 
				self.orderedRessources.extend( [(i,j) for i,j in zip(ressources, tmpfiles)] )
		print( "forms: ", len(self.newForms) )
		while len( self.newForms)>self.number :
			print("Forms insertion beginning")
			forms 	= [ self.newForms.popleft() for k in range(self.number) ]
			self.formManager.save(forms) 
		
	def run(self):
		logging.info("SQLHandler started")

		while not self.Exit.is_set():
			try:
				self.process()
			except Exception as e:
				logging.debug( e )	
				
			time.sleep( 1 )
		
		self.process()
		self.number=1
		self.process()
		logging.info("SQLHandler stopped")

class WorkerOverseer(Thread):
	def __init__(self, maxWorkers, dfs_path, orderedRessources, savedRessources,  Exit):
		"""
			@param maxWorkers			- maximun number of workers handled by this overseer
			@param orderedRessources	- ressources saved in db (see SQLHandler.preprocessing )
			@param savedRessources		- ressources saved in DFS
			@param Exit 				- stop condition( an event share with Slave, when Slave die it is set to true )
		"""
		Thread.__init__(self)

		self.orderedRessources	= orderedRessources
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
			w = Worker( self.dfs_path, self.orderedRessources, self.savedRessources, self.Exit )
			self.workers.append( w )
			w.start()
	
	def run(self):
		logging.info("WorkerOverseer started")

		self.process()
		while not self.Exit.is_set(): # pas encore de role definit en attente despécification utltérieures
			time.sleep( 1 ) 
		
		self.terminate()
		
class Worker(Thread):
	"""
		@brief saves a ressource on DFS
	"""
	def __init__(self, dfs_path, orderedRessources, savedRessources,  Exit):
		Thread.__init__(self)
		
		self.dfs_path			= dfs_path
		self.orderedRessources	= orderedRessources
		self.savedRessources	= savedRessources
		self.Exit 				= Exit
		
		logging.info("Worker initialized")

		
	def process(self):
		try:
			while True:
				print("Working yeahhhhhhhhhh")
				ressource, tmpFile = self.orderedRessources.popleft()
				print("|",self.dfs_path)
				ressource.save( self.dfs_path ) #build dir and metadata
				location = ressource.location( self.dfs_path )
				ressource.setFilename( location )
				
				if ressource.nature != pyHermes.t_Directory :
					with open(location, 'wb') as newFile:
						tmpFile.seek(0) 
						shutil.copyfileobj(tmpFile, newFile, 32768)
						tmpFile.close()
				else:
					not working
					dans le cas d'un dossier temporaire si nom alors le save marche très bien si setDir avant
				self.savedRessources.append( ressource )
		except Exception as e:
			logging.debug( e )
			print(e)
	
	def run(self):
		logging.info("Worker started")
		
		while not self.Exit.is_set():
			self.process()
			time.sleep(1)
			
		self.process()
		
class Out_Interface(AMQPProducer, Thread ):
	def __init__(self, savedRessources, Exit) :
		Thread.__init__(self)
		
		AMQPProducer.__init__(self, "artemis_out")
		self.channel.queue_declare(self.key, durable=False)
		
		self.savedRessources	= savedRessources
		self.Exit				= Exit
		
		logging.info("Out_Interface initialized")
		
	def add_tasks(self):
		while self.savedRessources:
			ressources = []
			try:
				for k in range( RESSOURCE_BUNDLE_LEN ) : 
					ressources.append( self.savedRessources.popleft() )
			except Exception :
				pass
			
			if ressources:
				self.add_task( Ressource.serialize(ressources) )
				
	def run(self):
		logging.info("Out_Interface started")
			
		while not self.Exit.is_set():
			self.add_tasks()
			sleep(1)
		
		#empty savedRessources
		RESSOURCE_BUNDLE_LEN = 1
		self.add_tasks()

class Server(Process, AMQPConsumer):
	def __init__(self, useragent, maxCrawlers, maxWorkers, delay, sqlNumber, dfs_path, contentTypes,
				domainRules, protocolRules, originRules, maxTasksSize, maxTorrentsSize, maxNewTasksSize, maxDoneTasksSize,
				maxNewFormsSize, maxUnorderedRessourcesSize, maxOrderedRessourcesSize, maxSavedRessourcesSize, maxActiveTorrents) :
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
		Process.__init__(self)
		AMQPConsumer.__init__(self)
		self.channel.exchange_declare(exchange='artemis_monitor_slave_out', type='fanout')
		self.channel.queue_bind(queue=self.key, exchange='artemis_monitor_slave_out')
		
		
		self.useragent			= useragent
		
		self.maxCrawlers		= maxCrawlers
		self.maxWorkers 		= maxWorkers
		
		self.delay				= delay
		self.sqlNumber			= sqlNumber
		self.dfs_path			= dfs_path
		
		self.netTree			= NetareaTree()
		self.contentTypes		= contentTypes
		self.domainRules		= domainRules
		self.protocolRules		= protocolRules
		self.originRules		= originRules
		
		self.maxActiveTorrents	= maxActiveTorrents
		
		self.tasks				= LimitedDeque( maxTasksSize )
		self.torrents			= LimitedDeque( maxTorrentsSize )
		self.maxTasks			= int(maxTasksSize / 2048) # assuming that an url len is less than 2048
		self.maxTorrents		= int(maxTasksSize / 4096) # assuming that an url len is less than 2048
		self.newTasks			= LimitedDeque( maxNewTasksSize )
		self.doneTasks			= LimitedDeque( maxDoneTasksSize )
		self.newForms			= LimitedDeque( maxNewFormsSize )
		self.unorderedRessources= {}
		self.orderedRessources	= LimitedDeque( maxOrderedRessourcesSize )
		self.savedRessources	= LimitedDeque( maxSavedRessourcesSize )
	
		

		self.In_Interface_Exit 				= Event()
		self.In_Torrent_Interface_Exit 		= Event()
		self.Sender_Exit 					= Event()
		self.CrawlerOverseer_Exit 			= Event()
		self.TorrentHandler_Exit 			= Event()
		self.SQLHandler_Exit 				= Event()
		self.WorkerOverseer_Exit 			= Event()
		self.Out_Interface_Exit				= Event()
		
		for key in range( NUM_CLASS_TYPES ):
			self.unorderedRessources[key]	= LimitedDeque( maxUnorderedRessourcesSize / NUM_CLASS_TYPES )
	
		self.running		= False # True when netTree received
		
		logging.info("Server initialized")

	def stop_sender(self):
		self.Sender_Exit.set()
		while self.sender.is_alive():
			time.sleep(1)
			
	def start_sender(self):
		self.sender	= Sender( self.newTasks, self.doneTasks, self.netTree, self.domainRules, self.protocolRules, self.originRules, 
			self.delay, self.Sender_Exit)
		self.sender.start()
		
	def terminate(self):
		self.In_Interface_Exit.set()
		while self.inInterface.is_alive():
			time.sleep(1)
			
		self.In_Torrent_Interface_Exit.set()
		while self.inInterface.is_alive():
			time.sleep(1)
		
		self.CrawlerOverseer_Exit.set()
		while self.crawlerOverseer.is_alive():
			time.sleep(1)
			
		self.TorrentHandler_Exit.set()
		while self.torrentHandler.is_alive():
			time.sleep(1)
		
		self.stop_sender()
			
		self.SQLHandler_Exit.set()
		while self.sqlHandler.is_alive():
			time.sleep(1)	
			
		self.WorkerOverseer_Exit.set()
		while self.workerOverseer.is_alive():
			time.sleep(1)
		
		self.Out_Interface_Exit.set()
		while self.outInterface.is_alive():
			time.sleep(1)
			
		Process.terminate(self)
	
	def harness(self):
		self.inInterface	= In_Interface( self.tasks, self.maxTasks, self.In_Interface_Exit)
		self.inTorrentInterface	= In_Torrent_Interface(self.torrents, self.maxTorrents, self.In_Torrent_Interface_Exit)
		self.crawlerOverseer= CrawlerOverseer( self.useragent, self.maxCrawlers,  self.tasks, self.doneTasks, self.newTasks,
			self.newForms, self.contentTypes, self.delay, self.unorderedRessources, self.CrawlerOverseer_Exit)
		self.torrentHandler	= TorrentHandler( self.torrents, self.contentTypes, self.maxActiveTorrents, self.useragent, self.doneTasks, self.newTasks, self.unorderedRessources, self.TorrentHandler_Exit)
		self.sqlHandler		= SQLHandler(self.sqlNumber, self.unorderedRessources, self.orderedRessources, self.newForms, self.SQLHandler_Exit)						
		self.workerOverseer	= WorkerOverseer( self.maxWorkers, self.dfs_path, self.orderedRessources, self.savedRessources,  self.WorkerOverseer_Exit)				
		self.outInterface	= Out_Interface( self.savedRessources, self.Out_Interface_Exit) 
		
		self.start_sender()
		
		self.inInterface.start()
		self.inTorrentInterface.start()
		self.crawlerOverseer.start()
		self.torrentHandler.start()
		self.sqlHandler.start()
		self.workerOverseer.start()
		self.outInterface.start()	
		
	def run(self):
		logging.info("Server started")
		
		self.channel.basic_consume(callback=self.proccess, queue=self.key, no_ack=True)
		#print("Waiting")
		while True: 
			self.channel.wait() 
	
	def proccess(self, msg):
		(header, args) =  unserialize( msg.body )
		AMQPConsumer.process( self, msg)
		#print("Monitor order received")
		
		if header == HEADER_SENDER_STOP and self.running:
			self.stop_sender()
		elif header == HEADER_SENDER_START and self.running:
			self.netTree.update(args)
			self.start_sender()	
		elif header == HEADER_SENDER_DEFAULT:
			#print("Nettree received")
			self.netTree.update(args)
			if not self.running and not args.empty():
				#print("running")
				self.harness()
				self.running= True
			
class Slave:
	def __init__(self, serverNumber=1, useragent="*", maxCrawlers=1, maxWorkers=2,
		delay=86400, sqlNumber=100, dfs_path="", contentTypes={"*":False}, domainRules={"*":False}, protocolRules={"*":False},
		originRules={"*":False}, maxTasksSize=1<<22, maxTorrentsSize=1<<22, maxNewTasksSize=1<<24, maxDoneTasksSize=1<<24,
		maxNewFormsSize=1<<22, maxUnorderedRessourcesSize=1<<26, maxOrderedRessourcesSize=1<<26, maxSavedRessourcesSize=1<<26,
		maxActiveTorrents=8 ) :
		
		self.pool			= []
		self.serverNumber 	= serverNumber
		
		for i in range(self.serverNumber):
			s = Server(useragent, maxCrawlers, maxWorkers, delay, sqlNumber, dfs_path, contentTypes,
				domainRules, protocolRules, originRules, maxTasksSize, maxTorrentsSize, maxNewTasksSize, maxDoneTasksSize, maxNewFormsSize,
				maxUnorderedRessourcesSize, maxOrderedRessourcesSize, maxSavedRessourcesSize, maxActiveTorrents)
			self.pool.append( s )
		
		logging.info("Slave initialized")


	def terminate(self):
		for server in self.pool:
			server.terminate() if server.is_alive() else () 
		logging.info("Servers stoped")

	def harness(self):
		logging.info("Slave started")

		for s in self.pool:
			s.start()
			
		while True:
			sleep(10)
