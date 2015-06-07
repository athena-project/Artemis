import sys
import collections
import os
from .AMQPConsumer import *
from .AMQPProducer import *
from .Netarea import *


from .Mtype import *

from .RobotCacheHandler import *
from threading import Thread, RLock, Event
from multiprocessing import Process, Queue

from .Utility import serialize, unserialize

#os.setpriority
#os.cpu_count()
#os.getloadavg()

URL_BUNDLE_LEN = 10 #url

class Master(AMQPConsumer):
	"""
		@param maxRam used by this server
		@param maxCore max core used by this server
	"""
	ip					="127.0.0.1"
	pool				= []
	Monitor_out_Exit	= Event()
	
	def __init__(self, ip="127.0.0.1", netareas=[], useragent="*",  domainRules={"*":False},
	protocolRules={"*":False}, originRules={"*":False}, delay = 36000,
	maxNumNetareas=2, maxRamNetarea=1<<27):
		AMQPConsumer.__init__(self)
		self.channel.exchange_declare(exchange='artemis_monitor_master_out', type='direct')
		self.channel.queue_bind(queue=self.key, exchange='artemis_monitor_master_out', routing_key=self.ip)
		
		self.ip					= ip
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
		self.netarea_order 		={} # key=> Value!=None then value=net_tree et prune needed
		for netarea in netareas :
			self.start_netareamanager( netarea )

		self.monitor_out	= Monitor_out( self.ip, os.cpu_count(), 0, self.maxNumNetareas, self.netarea_reports, self.Monitor_out_Exit)
	
	def start_netareamanager(self, netarea):
		maxInUrlsSize	= Mint(0.025 * self.maxRamNetarea) #1<<22	#maxInUrlsSize 4Mb
		maxDoneUrlsSize	= Mint(0.025 * self.maxRamNetarea) #1<<22	#maxDoneUrlsSize 4Mb
		maxOutUrlsSize	= Mint(0.025 * self.maxRamNetarea) #1<<22	#maxOutUrlsSize 4Mb
		maxRobotsSize	= Mint(0.025 * self.maxRamNetarea) #1<<22 #maxRobotsSize 4Mb
		maxUrlsMapSize	= Mint(0.900 * self.maxRamNetarea) #Mint(1<<27) #maxUrlMapsSize 128Mb
					
		order = NetareaTree()
				
		s = NetareaManager( netarea.netarea, self.in_workers, self.done_workers, self.out_workers, maxInUrlsSize, maxDoneUrlsSize, maxOutUrlsSize, self.useragent, self.domainRules,
				self.protocolRules, self.originRules, self.delay, maxUrlsMapSize, maxRobotsSize, netarea, order)
		
		self.netarea_reports[ netarea.netarea ] = netarea 
		self.netarea_order[ netarea.netarea ] = order 
		self.pool.append( s )
		s.start()
		
	def terminate(self):
		self.Monitor_out_Exit.set()
		for netareaManager in self.pool:
			netareaManager.terminate() if netareaManager.is_alive() else () 
		logging.info("NetareaManagers stoped")
	
	def harness(self):
		for (m,netareaManager) in self.pool:
			netareaManager.start()
		logging.info("NetareaManagers started")
		print("hello")
		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while True:
			self.channel.wait()
	
	def proccess(self, msg):
		header, args	= unserialize( msg )
		self.monitor_tr = (report, netTree)
		AMQPConsumer.process( self, msg)
		
		if header == HEADER_NETAREA_PROPAGATION:
			(netareas, net_tree) = args
			for netarea in netareas:
				if netarea.netarea in self.netarea_reports:
					if netarea.next_netarea != self.netarea_reports[ netarea.netarea ]: #modified
						self.netarea_reports[ netarea.netarea ].next_netarea 		= netarea.next_netarea
						self.netarea_reports[ netarea.netarea ].int_next_netarea 	= netarea.int_next_netarea
						self.netarea_reports[ netarea.netarea ].used_ram 			= 0 
						
						self.orders[ netarea.netarea ]								= net_tree
					else :
						self.start_netareamanager( netarea )
	
class Monitor_out(AMQPProducer,Thread):
	def __init__(self, ip, num_core, maxRam, maxNumNetareas, netarea_reports, Exit) :
		"""
			@param net_area id that descibe the partition of the net managed by this master
			@param in_urls			incomming RecordUrl type
		"""		
		Thread.__init__(self)
		AMQPProducer.__init__(self,"artemis_monitor_in")
		
		self.ip				= ip
		self.num_core		= num_core
		self.maxRam			= maxRam
		self.maxNumNetareas	= maxNumNetareas
		self.netarea_reports= netarea_reports
	
	def terminate(self):
		AMQPProducer.terminate(self)

	def run(self):
		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while not self.Exit.is_set():
			report = MasterReport( self.ip, self.num_core, self.maxRam, self.maxNumNetareas, self.netarea_reports.values() )
			self.producer.add_task( serialize( report ) )
			time.sleep(1)
		
	def proccess(self, msg):
		(report, netTree)	= unserialize( msg )
		self.monitor_tr = (report, netTree)
		
		AMQPConsumer.process( self, msg)
	
class NetareaManager(Process, AMQPProducer):
	"""
		Warning : One netareamanager by netarea on the whole network
	"""
	Exit				= Event()
	def __init__(self, netarea, in_workers, done_workers, out_workers, maxInUrlsSize, maxDoneUrlsSize, maxOutUrlsSize, useragent, domainRules,
					protocolRules, originRules, delay, maxUrlsMapSize, maxRobotsSize, netarea_report, order) :
		"""
			@param netarea			- netarea object, its id is uniq
			@param useragent		- 
			@param domainRules		- { "domain1" : bool (true ie allowed False forbiden) }, "*" is the default rule
			@param protocolRules	- { "protocol1" : bool (true ie allowed False forbiden) }, "*" is the default protocol
			@param originRules		- { "origin1" : bool (true ie allowed False forbiden) }, "*" is the default origin,
				the origin is the parent balise of the url
			@param delay			- period between two crawl of the same page
			@param maxRamSize		- maxsize of the urls list kept in ram( in Bytes )
			@param numOverseer		- 
		"""
		Process.__init__(self)
		
		self.in_urls			= LimitedDeque( maxInUrlsSize )
		self.done_urls			= LimitedDeque( maxDoneUrlsSize )
		self.out_urls			= LimitedDeque( maxOutUrlsSize )
		self.InExit				= Event()
		self.ValidatorExit		= Event()
		self.OutExit		    = Event()
		
		self.report				= netarea_report
		self.order				= order
		
		self.in_pool			= [ In_Worker(net_area, self.in_urls, self.InExit ) for k in range(in_workers) ]	
		self.done_pool			= [ Done_Worker(net_area, self.done_urls, self.DoneExit ) for k in range(done_workers) ]	
		sef.validator			= Validator(useragent, domainRules, protocolRules, originRules, delay,
											maxUrlsMapSize, maxRobotsSize, self.in_urls, self.done_urls, self.out_urls,
											self.report, self.order, self.ValidatorExit )	
		self.out_pool			= [ Out_Worker(self.out_urls, self.OutExit ) for k in range(out_workers) ]	
		
		
	def __del__(self):
		self.terminate()
	
	def terminate(self):
		self.InExit.set()
		while self.in_pool :
			for w in in_pool:
				self.in_pool.remove( w ) if not w.is_alive() else ()
			sleep(0.1) if self.in_pool else () 
		
		self.DoneExit.set()
		while self.done_pool :
			for w in done_pool:
				self.done_pool.remove( w ) if not w.is_alive() else ()
			sleep(0.1) if self.done_pool else ()
		
		self.ValidatorExit.set()
		while self.validator.is_alive():
			sleep(0.1)
		
		self.OutExit.set()
		while self.out_workers != 0:
			for w in self.out_workers:
				self.out_workers.remove( w ) if not w.is_alive() else ()
			sleep(0.1) if self.out_workers else () 
			
		Process.terminate(self)
	
	def run(self):
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
	def __init__(self, net_area, in_urls, Exit) :
		"""
			@param net_area id that descibe the partition of the net managed by this master
			@param in_urls			incomming RecordUrl type
		"""		
		Thread.__init__(self)
		
		AMQPConsumer.__init__(self, "artemis_master_in")
		self.channel.exchange_declare(exchange='artemis_master_in_direct', type='direct')
		self.channel.queue_declare(self.key, durable=False)
		self.channel.queue_bind(queue='artemis_master_in', exchange='artemis_master_in_direct', routing_key=net_area)
		
		self.net_area			= net_area
		self.in_urls			= in_urls
		self.Exit				= Exit
		
	def run(self):
		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while not self.Exit.is_set():
			self.channel.wait()
		
	def proccess(self, msg):
		self.in_urls.append( Url.unserialize( msg.body ) )
		AMQPConsumer.process( self, msg)
	
class Done_Worker(AMQPConsumer, Thread ):
	def __init__(self, net_area, done_urls, Exit) :
		"""
			@param net_area id that descibe the partition of the net managed by this master
			@param done_urls			[ [url,urls] ] incomming RecordUrl type
		"""		
		Thread.__init__(self)
		
		AMQPConsumer.__init__(self, "artemis_master_done")
		self.channel.exchange_declare(exchange='artemis_master_done_direct', type='direct')
		self.channel.queue_declare(self.key, durable=False)
		self.channel.queue_bind(queue='artemis_master_done', exchange='artemis_master_done_direct', routing_key=net_area)
		
		self.net_area			= net_area
		self.done_urls			= done_urls
		self.Exit				= Exit
		
	def run(self):
		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while not self.Exit.is_set():
			self.channel.wait()
		
	def proccess(self, msg):
		self.done_urls.append( Url.unserialize( msg.body ) )
		AMQPConsumer.process( self, msg)
			
class Validator( Thread ):
	"""
		@brief One validator per Server
	"""
	def __init__(self, useragent, delay,
				maxUrlsMapSize, maxRobotsSize, in_urls, done_urls, out_urls, report, order, Exit) :
		"""
			@param useragent		- 
			@param delay			- default period between two crawl of the same page
			@param maxRamSize		- maxsize of the urls list kept in ram( in Bytes )
			@param in_urls			- urls incomming
			@param done_urls		- urls crawled
			@param out_urls			processed urls
		"""
		Thread.__init__(self)
		
		self.useragent 			= useragent
		self.delay				= delay # de maj
		
		self.maxRamSize			= maxRamSize
		
		self.urlsMap			= LimitedDict( maxUrlsMapSize ) 
		self.in_urls			= in_urls
		self.done_urls			= done_urls
		self.out_urls			= out_urls
		self.robotsMap			= RobotCacheHandler( maxRobotsSize )	
		
		self.report				= report
		self.order				= order
		self.Exit				= Exit
		
	def is_valid(self, urlRecord):
		url = urlRecord.url
		if( url in self.urlsMap and  self.urlsMap[url].is_alive(self.delay) ):
			return False
		
		urlP = urlparse( url )
		robot_url = urlP.scheme+"://"+urlP.netloc+"/robots.txt"
		if robot_url not in self.robotsmap:
			sitemap = self.robotsmap.add(robot_url)
			self.in_urls.append( UrlRecord(sitemap) )
			
		if not self.robotsmap[robot_url].can_fetch(self.useragent , url):
			return False
		
		urlRecord.lastcontrolled = time.time()
		self.urlsMap[url]=urlRecord
		return True
	
	def validate(self):
		while self.in_urls :
			urlRecord =  self.in_url.popleft()
			if self.is_valid( urlRecord ):
				self.out_urls.append( urlRecord )
	
	def refresh(self):
		"""
			@brief Update the urlMap with done_urls
		"""
		while self.done_urls :
			urlRecord =  self.done_url.popleft()
			self.urlsMap[urlRecord.url] = urlRecord 
			
	def update(self): 
		"""
			@brief update of the map, ie maj of the url already store
		"""
		for (key,item) in self.urlsMap.iteritems() :
			urlRecord = item[1]
			if self.is_valid( urlRecord ):
				self.out_urls.append( urlRecord )
			
	def run(self):
		while not self.Exit.is_set():
			if self.order.hight != -1 :
				self.prune()
				
			self.refresh()
			self.validate()
			self.update()
			
			self.report.used_ram =  self.in_urls.mem_length + self.done_urls.mem_length
			self.report.used_ram += self.out_urls.mem_length +self.robotsMap.mem_length
			self.report.used_ram += self.urlsMap.mem_length  
			sleep( 1 )
			
		#empty in_urls
		self.refresh()
		self.validate()	
	
	def prune(self):
		"""
			When the current netarea is split send  the url not needed 
		"""
		self.done_producer			= AMQPProducer.AMQPProducer("artemis_master_done")
		self.done_producer.channel.exchange_declare(exchange='artemis_master_done_direct', type='direct')
		self.done_producer.channel.queue_declare("artemis_master_done", durable=False)
		
		for url in self.urlsMap.keys():
			key	= self.order.search( Phi(urlRecord) ).netarea
			if key != report.netarea :
				self.new_producer.add_task( serialize( self.urlsMap[url] ), echange="artemis_master_done_direct", routing_key=key  )
				self.urlsMap.pop( url )
		
class Out_Worker(AMQPProducer, Thread ):
	def __init__(self, out_urls, Exit) :
		"""
			@param out_urls			
		"""		
		Thread.__init__(self)
		
		AMQPProducer.__init__(self, "artemis_master_out")
		self.channel.queue_declare(self.key, durable=False)
		
		self.out_urls			= out_urls
		self.Exit				= Exit
		
	def add_tasks(self):
		while self.out_urls:
			urls = []
			try:
				for k in range( URL_BUNDLE_LEN ) : 
					urls.append( self.out_urls.popleft() )
			except Exception :
				pass
			
			if urls:
				self.add_task( Url.serializeList(urls) )
				
	def run(self):
		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while not self.Exit.is_set():
			self.add_tasks()
			sleep(1)
		
		#empty out_urls
		URL_BUNDLE_LEN=1
		self.add_tasks()
		
	
