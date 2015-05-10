import sys
import collections
import os
from AMQPConsumer import *
from AMQPProducer import *
from AVL import *


import RobotCacheHandler
from threading import Thread, RLock, Event
from multiprocessing import Process, Queue


class In_Monitor(AMQPConsumer, Thread ):
	def __init__(self, reports, Exit) :
		"""
			@param reports	dict of master reports [id_master=>last report]
		"""		
		Thread.__init__(self)
		
		AMQPConsumer.__init__(self, "artemis_monitor_in")
		self.channel.queue_declare(self.key, durable=False)
		
		self.reports			= reports
		self.Exit				= Exit
		
	def run(self):
		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while not self.Exit.is_set():
			self.channel.wait()
		
	def proccess(self, msg):
		report = unserialise( msg.body )
		self.reports[ report.id  ] = report
		AMQPConsumer.process( self, msg)

class Monitor:
	def __init__(self, in_workers):
		
		self.in_pool	=[]
		self.reports 	= {} #received reports from masters
		self.Exit 		= Exit()
		
		self.producer	= AMQPProducer.__init__(self, "artemis_monitor_out")
		self.producer.channel.exchange_declare(exchange='artemis_monitor_master_out', type='direct')
		self.producer.channel.exchange_declare(exchange='artemis_monitor_slave_out', type='fanout')

		
		for k in range(in_workers):
			self.in_pool.append( In_Monitor(self.reports, self.Exit)
	
	def is_overload(self):
		for reports in self.reports.values():
			if repot.is_overload():
				return True
		return False
		
	def localized_loadbalancing(self):
		copy_master_reports = copy.deepcopy( self.reports.values() ) # instantané
		overload_netareas = []
		for master in copy_master_reports:
			master.garbage_collector(coef)
			
			for netarea in mastre.netarea_reports:
				if netarea.overload():
					overload_netareas.append( netarea )
					master.netarea_reports.suppr(netare)
					
			master.calcul_used_ram()
			master.calcul_free_ram()
			if master.free_ram > 0:
				free_masters.append(master)
				
		free_maters.sort(key=lambda master: -1*master.free_ram) 
		overload_netareas.sort(key=lambda netarea: -1*(1+netarea.load()-coef)*netarea.max_ram)
		
		for netarea in overload_netareas:
			needed_ram = (1+netarea.load()-coef) * netarea.max_ram
			if needed_ram < free_masters[0].free_ram :
				free_masters[0].netarea_reports.append( needed_ram )
				
				master.calcul_used_ram()
				master.calcul_free_ram()
				free_maters.sort(key=lambda master: -1*master.free_ram) 
			elif coef<0.8 :
				global_loadbalancing_1(coef+0.1, master_reports)
			else:
				return (False, None)
				
		return (True, copy_master_reports)
	
	def global_loadbalancing(self):
		netareas = []
		masters  = []
		global_max_ram = 0
		
		masters.append( copy.deepcopy(self.reports.values()) )
		masters[-1].netareas_reports = [] 
		
		needed_ram=0
		for netarea in netareas:
			needed_ram += (1+netarea.load()-coef) * netarea.max_ram
			
		#Si une solution peut être trouvée
		if needed_ram>global_max_ram:
			return (False, None)
		
		netareas.sort(key=lambda netarea : -1*(1+netarea.load()-coef) * netarea.max_ram)
		netareas_n=netareas
		netarea_n.sort((key=lambda netarea :netarea.netarea)
		masters.sort(key=lambda master : -1*master.max_ram)
		
		#Allocation de la plus lourde netarea au master le plus robuste
		while netareas:
			netarea = netareas.pop()
			if 1+netarea.load()-coef) * netarea.max_ram < masters[0].max_ram : #on alloue
				masters[0].netareas_reports.append( netarea )
			else: #il faut decouper
				index = netareas_n.index( netarea) +1
				next_netarea = netareas_n[ index ] if index < len(next_netarea) else MAX
				netareas.extend( netarea.split( (1-coef) * masters[0].max_ram ,next_netarea ) )
			
			netareas.sort(key=lambda netarea : -1*(1+netarea.load()-coef) * netarea.max_ram) # ici on pourrait réinserer à la bonne place (dichotomie) pour eviter les trie
			masters.sort(key=lambda master : -1*master.max_ram)
		
		return (True, masters)
		
	def balance(self):
		if not self.is_overload():
			return 
		
		flag, new_reports = self.localized_loadbalancing()
		if not flag:
			flag, new_reports = self.global_loadbalancing()
		
		if not flag:
			logging.critical("System overloaded - new master needed")
		
		net_tree = NetareaTree()
		for master in new_reports:
			self.producer.add_task( serialize( master ) , echange="artemis_monitor_master_out", routing_key=master.ip  )
			for netarea in master.netarea_reports:
				net_tree[netarea.netarea]=netarea
		
		#va falloir un truc pour synchroniser
		
		self.producer.add_task( serialize(net_tree) , echange="artemis_monitor_slave_out")
		
		return (new_reports, net_tree)
		
		

	def run(self):
		for w in self.in_pool:
			w.start()
		
		while True:
			self.balance()
			time.sleep(30)
