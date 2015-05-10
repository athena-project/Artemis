import sys
import collections
import os
from AMQPConsumer import *
from AMQPProducer import *
from AVL import *


import Mtype

import RobotCacheHandler
from threading import Thread, RLock, Event
from multiprocessing import Process, Queue

#os.setpriority
#os.cpu_count()
#os.getloadavg()





URL_BUNDLE_LEN = 10 #url


###
### For now we assume that the netarea are staticaly build, after we must adapt the area 
###
#class NetareaReport:
	#def __init__(self, netarea, max_ram=0, used_ram=0):
		#self.netarea = netarea
	
	#def weight(self):
		#return (self.max_ram-self.used_ram) / self.max_ram
	
	#def serialize(self):
		#return pickle.dumps( l )


#class Health_Monitor(AMQPProducer, Thread):
	#def __init__(self, Exit) :
		#Thread.__init__(self)
		
		#AMQPConsumer.__init__(self, "artemis_health")
		#self.channel.exchange_declare(exchange='artemis_health_direct', type='direct')
		##self.channel.queue_declare(self.key, durable=True) already in parent 
		#self.channel.queue_bind(queue='artemis_health', exchange='artemis_health_direct', routing_key="master")
		
		
		#self.netareaMap			= {} # unique id, 
		#self.netareaTree		= NetareaNode()
		
		#self.Exit				= Exit
		
	#def run(self):
		#self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		#while not self.Exit.is_set():
			#self.channel.wait()
		
	#def proccess(self, ch, method, properties, body):
		##method.routing_key
		#report = pickle.loads( l )
		#self.netareaMap[ report.netarea ] = report


class PerfMonitor:
	def __init(self):
		self.ram = 0

class Master:
	"""
		@param maxRam used by this server
		@param maxCore max core used by this server
	"""
	def __init__(self, netareas=[], useragent="*",  domainRules={"*":False}, protocolRules={"*":False}, originRules={"*":False}, delay = 36000, maxRam=1<<30, maxCore=-1):
		
		self.maxRam			= maxRam
		self.maxCore		= os.cpu_count() if maxCore == -1 else maxCore #One netarea per core, will be needed when load balncing area
		
		self.pool			= []
		
		
		in_workers		= 4
		done_workers	= 2
		out_workers		= 2
		
		maxRamManager	= int(maxRam / len(netareas))
		
		
		for netarea in netareas :
			maxInUrlsSize	= Mint(0.025 * maxRam) #1<<22	#maxInUrlsSize 4Mb
			maxDoneUrlsSize	= Mint(0.025 * maxRam) #1<<22	#maxDoneUrlsSize 4Mb
			maxOutUrlsSize	= Mint(0.025 * maxRam) #1<<22	#maxOutUrlsSize 4Mb
			maxRobotsSize	= Mint(0.025 * maxRam) #1<<22 #maxRobotsSize 4Mb
			maxUrlsMapSize	= Mint(0.900 * maxRam) #Mint(1<<27) #maxUrlMapsSize 128Mb
			netarea_report = NetareaReport(netarea, 0, maxInUrlsSize+maxDoneUrlsSize+maxOutUrlsSize+maxRobotsSize+maxUrlsMapSize)
			s = NetareaManager( netarea, in_workers, done_workers, out_workers, maxInUrlsSize, maxDoneUrlsSize, maxOutUrlsSize, useragent, period, domainRules,
					protocolRules, originRules, delay, maxUrlsMapSize, maxRobotsSize, netarea_report)
			self.pool.append( (maxInUrlsSize, maxDoneUrlsSize, maxOutUrlsSize, maxRobotsSize, maxUrlsMapSize, s) ) 
			self.netarea_reports.append( netarea_report )
			
		
	
	def __del__(self):
		for netareaManager in self.pool:
			netareaManager.terminate() if netareaManager.is_alive() else () 
		logging.info("NetareaManagers stoped")
	
	def harness(self):
		for (m,netareaManager) in self.pool:
			netareaManager.start()
		logging.info("NetareaManagers started")
		self.pool[0].join()
	
	
	def balance(self):
		while i<len(master_reports) and not GLOBAL_LOADBALANCING:
	GLOBAL_LOADBALANCING = master_reports[i].is_overload()
	i+=1
		
		if self.local_balance(0.5):
			for ((m1, m2, m3, m4, m4, m5, report),netareaMangager) in (self.netarea_reports, self.pool):
				m1.value = report.max_ram * 0.025
				m2.value = report.max_ram * 0.025
				m3.value = report.max_ram * 0.025
				m4.value = report.max_ram * 0.025
				m5.value = report.max_ram * 0.9
				
				
	def local_balance(self, coef):
		"""
			Balance ressources between running netmanager
			between coef and max_coef =0.95
		"""
		
		master = MasterReport( self.ip, self.num_core, self.maxRam, self.netarea_reports)
		overload_netareas = []
		
		for netarea in self.netarea_reports:
			if netarea.
			ram_needed = (netarea.load()-coef) * netarea.max_ram
			if ram_needed < 0:
				pass
			elif master.free_ram > ram_needed:
				netarea.max_ram	+= ram_needed
				master.calcul_used_ram()
				master.calcul_free_ram()
			elif master.garbage_collector():
				local_loadbalancing(coef, master)
			elif coef<0.95 :
				local_loadbalancing( coef+0.5, master )
			else:
				return False
		
		return True
	
class NetareaManager(Process, AMQPProducer):
	"""
		Warning : One netareamanager by netarea on the whole network
	"""
	Exit				= Event()
	def __init__(self, netarea, in_workers, done_workers, out_workers, maxInUrlsSize, maxDoneUrlsSize, maxOutUrlsSize, useragent, period, domainRules,
					protocolRules, originRules, delay, maxUrlsMapSize, maxRobotsSize, netarea_report) :
		"""
			@param netarea			- netarea object, its id is uniq
			@param useragent		- 
			@param period			- period between to wake up
			@param domainRules		- { "domain1" : bool (true ie allowed False forbiden) }, "*" is the default rule
			@param protocolRules	- { "protocol1" : bool (true ie allowed False forbiden) }, "*" is the default protocol
			@param originRules		- { "origin1" : bool (true ie allowed False forbiden) }, "*" is the default origin,
				the origin is the parent balise of the url
			@param delay			- period between two crawl of the same page
			@param maxRamSize		- maxsize of the urls list kept in ram( in Bytes )
			@param numOverseer		- 
		"""
		Process.__init__(self)
		#AMQPProducer.__init__(self, "artemis_health") when we will use dynamic netarea
		#self.channel.exchange_declare(exchange='artemis_health_direct', type='direct')
		#self.channel.queue_declare(self.key, durable=False)
		
		self.in_urls			= LimitedDeque( maxInUrlsSize )
		self.done_urls			= LimitedDeque( maxDoneUrlsSize )
		self.out_urls			= LimitedDeque( maxOutUrlsSize )
		self.InExit				= Event()
		self.ValidatorExit		= Event()
		self.OutExit		    = Event()
		
		self.report		= netarea_report
		
		self.in_pool			= [ In_Worker(net_area, self.in_urls, self.InExit ) for k in range(in_workers) ]	
		self.done_pool			= [ Done_Worker(net_area, self.done_urls, self.DoneExit ) for k in range(done_workers) ]	
		sef.validator			= Validator(useragent, period, domainRules, protocolRules, originRules, delay,
											maxUrlsMapSize, maxRobotsSize, self.in_urls, self.done_urls, self.out_urls,
											self.report, self.ValidatorExit )	
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
			
		#max_ram = self.maxInUrlsSize + self.maxOutUrlsSize + self.maxUrlsMapSize + self.maxRobotsSize
		#self.channel.basic_consume(callback=self.proccess, queue=self.key)

		while True:
			#self.add_task( HealthReport(self.net_area, max_ram ), echange="artemis_health_direct", routing_key="master" )
			sleep(10) #for now, after load balancing of network area and  helathreoport to the Master

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
	def __init__(self, useragent, period, delay,
				maxUrlsMapSize, maxRobotsSize, in_urls, done_urls, out_urls, report, Exit) :
		"""
			@param useragent		- 
			@param period			- period between to wake up
			@param delay			- default period between two crawl of the same page
			@param maxRamSize		- maxsize of the urls list kept in ram( in Bytes )
			@param in_urls			- urls incomming
			@param done_urls		- urls crawled
			@param out_urls			processed urls
		"""
		Thread.__init__(self)
		
		self.useragent 			= useragent
		self.period				= period # delay(second) betwen two crawl
		self.delay				= delay # de maj
		
		self.maxRamSize			= maxRamSize
		
		self.urlsMap			= LimitedDict( maxUrlsMapSize ) 
		self.in_urls			= in_urls
		self.done_urls			= done_urls
		self.out_urls			= out_urls
		self.robotsMap			= RobotCacheHandler( maxRobotsSize )	
		
		self.report		= report
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
		
	
