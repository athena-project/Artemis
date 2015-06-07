import sys
import collections
import os
from AMQPConsumer import *
from AMQPProducer import *
from AVL import *


import RobotCacheHandler
from threading import Thread, RLock, Event
from multiprocessing import Process, Queue

HEADER_SENDER_STOP 	= 0x0
HEADER_SENDER_START	= 0x1#argument net_tree
HEADER_NETAREA_PROPAGATION = 0x2#argument netareas reports

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
	def __init__(self, in_monitors, limitFreeMasters):
		
		self.in_pool	=[]
		self.reports 	= {} #received reports from masters
		self.limitFreeMasters = limitFreeMasters
		self.Exit 		= Exit()
		
		self.producer	= AMQPProducer.__init__(self, "artemis_monitor_out")
		self.producer.channel.exchange_declare(exchange='artemis_monitor_master_out', type='direct')
		self.producer.channel.exchange_declare(exchange='artemis_monitor_slave_out', type='fanout')

		
		for k in range(in_monitors):
			self.in_pool.append( In_Monitor(self.reports, self.Exit) )
	
	def is_overload(self):
		for report in self.reports.values():
			for netarea in report.netarea_reports:
				if netarea.is_overload():
					return True
		return False
		
	def balance(self):
		if not self.is_overload():
			return 
		
		masters =  copy.deepcopy(self.reports.values())
		unallocated_netarea	= []

		for master in masters:
			for netarea in master.netarea_reports:
				if netarea.is_overload():
					net1	= netarea.split()
					
					if not master.is_overload():
						master.allocate( net1 )
					else:
						unallocated_netarea.append(net1)
		
		free_masters = [ master for master in masters if not master.is_overload() ]
		try:
			for netarea in unallocated_netarea:
				free_masters[-1].allocate( netarea )
				free_masters.pop() if free_masters[-1].is_overload() else ()
			
			if sum([ int(not master.is_overload()) for master in masters ]) < self.limitFreeMasters:
				logging.warning( "Masters should be added, system will be soon overload")
			
		except Exception: # if not a free_master remains
			logging.critical( "Masters must be added, system is overload")
		
		return masters
		
	def propagate(self, masters):
		net_tree = NetareaTree()
		for master in masters:
			for netarea in master.netarea_reports:
				net_tree[netarea.netarea]=netarea
		
		#Stop Slave.sender
		header 	= HEADER_SENDER_STOP
		args 	= None
		self.producer.add_task( serialize( (header, args) ) , echange="artemis_monitor_slave_out")
		time.sleep(12)
		 
		#Start new netarea
		for master in masters:
			header 	= HEADER_NETAREA_PROPAGATION
			args 	= (master, net_tree)
			self.producer.add_task( serialize( (header, args) ) , echange="artemis_monitor_master_out", routing_key=master.ip  )
		time.sleep(12)
		
		#Start Slave.sender
		header 	= HEADER_SENDER_START
		args 	= net_tree
		self.producer.add_task( serialize( (header, args) ) , echange="artemis_monitor_slave_out")
		
	def run(self):
		for w in self.in_pool:
			w.start()
		
		while True:
			self.balance()
			time.sleep(60)
