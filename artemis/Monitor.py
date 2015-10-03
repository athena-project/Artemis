import sys
import collections
import os
from .network.AMQPConsumer import *
from .network.AMQPProducer import *
from .AVL import *

from time import sleep
import artemis.RobotCacheHandler
from threading import Thread, RLock, Event
from multiprocessing import Process, Queue
from .Utility import serialize, unserialize
from copy import deepcopy
from math import ceil
from .Netarea import NetareaReport, NetareaTree, MAX as NETAREA_MAX

HEADER_SENDER_STOP 	= 0x0
HEADER_SENDER_START	= 0x01 #argument net_tree
HEADER_SENDER_DEFAULT=0x011
HEADER_NETAREA_PROPAGATION = 0x2 #argument netareas reports

FIRST_RATE			= 0.6 #proportion de netarea alloué la première fois

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
		
		logging.debug("In_Monitor initialized")

	def run(self):
		logging.debug("In_Monitor started")

		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		
		while not self.Exit.is_set():
			self.channel.wait()
		
	def proccess(self, msg):
		report = unserialize( msg.body )
		self.reports[ report.id  ] = report
		print( report)
		print()
		AMQPConsumer.process( self, msg)


class Slave_out(AMQPProducer,Thread):
	def __init__(self, net_tree, Exit) :
		"""
			@param net_area id that descibe the partition of the net managed by this master
			@param in_tasks			incomming RecordTask type
		"""		
		Thread.__init__(self)
		AMQPProducer.__init__(self,"artemis_monitor_slave_out")
		self.channel.exchange_declare(exchange='artemis_monitor_slave_out', type='fanout')
		
		self.net_tree		= net_tree
		self.Exit			= Exit
		
		logging.debug("Monitor_out initialized")

	def terminate(self):
		AMQPProducer.terminate(self)

	def run(self):
		logging.debug("Monitor_out started")
				
		while not self.Exit.is_set():
			header 	= HEADER_SENDER_DEFAULT
			args 	= self.net_tree
			self.add_task_fanout( serialize( (header, args) ) , exchange="artemis_monitor_slave_out")
			sleep(1)

class Monitor:
	def __init__(self, in_monitors, limitFreeMasters):
		"""
			@param limitFreeMasters - minimum number of master which are not overload in the cluster
		"""
		
		self.in_pool	=[]
		self.reports 	= {} #received reports from masters
		self.limitFreeMasters = limitFreeMasters
		self.Exit 		= Event()
		
		self.producer	= AMQPProducer("artemis_monitor_out")
		self.producer.channel.exchange_declare(exchange='artemis_monitor_master_out', type='direct')
		self.producer.channel.exchange_declare(exchange='artemis_monitor_slave_out', type='fanout')
		
		self.net_tree	= NetareaTree()
		self.slave_out	= Slave_out(self.net_tree, self.Exit)
		
		for k in range(in_monitors):
			self.in_pool.append( In_Monitor(self.reports, self.Exit) )
		
		logging.debug("Monitor initialized")

		
	def is_overload(self):
		for report in self.reports.values():
			for netarea in report.netarea_reports:
				if netarea.is_overload():
					return True
		return False
		
	def first_allocation(self):
		max_netareas	= sum([ r.maxNumNetareas for r in self.reports.values() ])
		if max_netareas == 0:
			return
		print("First Allocation done")
		
		free_netareas	= int( FIRST_RATE * max_netareas )
		masters 		=  deepcopy( list(self.reports.values() ))
		i				= 0
		
		begin			= 0
		step			= ceil(NETAREA_MAX / float(max_netareas-free_netareas))

		for master in masters:
			for j in range( master.maxNumNetareas ):
				if  i < max_netareas-free_netareas :
					net	=NetareaReport(begin,0, 1<<25, begin+step)
					master.allocate( net )
					begin	+= step
					i+=1
					print("i ",i)
				else:
					break
		print( len(masters[0].netarea_reports))
		self.propagate(masters)
		
	def allocate(self, masters, unallocated_netarea):
		free_masters = [ master for master in masters if not master.is_overload() and not master.is_expired() ]
		try:
			for netarea in unallocated_netarea:
				free_masters[-1].allocate( netarea )
				free_masters.pop() if free_masters[-1].is_overload() else ()
			
			if sum([ int(not master.is_overload()) for master in masters ]) < self.limitFreeMasters:
				logging.warning( "Masters should be added, system will be soon overload")
			
		except Exception: # if not a free_master remains
			logging.critical( "Masters must be added, system is overload")
		
	def detect(self):
		"""
			masters' fualt
		"""
		unallocated_netarea	= [ net for key,report in self.reports.items() if( report.is_expired()) for net in report.netarea_reports ]
		del_key				= [ key for key,report in self.reports.items() if( report.is_expired()) ]
		for key in del_key:
			del self.reports[key]
				
		masters =  deepcopy( list(self.reports.values() ))
		if unallocated_netarea:
			self.allocate( masters, unallocated_netarea)
		
		return masters
		
	def balance(self):
		if sum([ len(r.netarea_reports) for r in self.reports.values() ]) == 0:
			self.first_allocation()#No netarea allocated
			return
		
		if not self.is_overload():
			return 
		
		masters =  deepcopy( list(self.reports.values() ))
		unallocated_netarea	= []

		for master in masters:
			for netarea in master.netarea_reports:
				if netarea.is_overload():
					net1	= netarea.split()
					
					if not master.is_overload():
						master.allocate( net1 )
					else:
						unallocated_netarea.append(net1)
		
		self.allocate( masters, unallocated_netarea)
		
		return masters
		
	def propagate(self, masters):
		print("propagat")
		net_tree = NetareaTree()
		for master in masters:
			for netarea in master.netarea_reports:
				net_tree[netarea.netarea]=netarea
				
		self.net_tree.update( net_tree )
		
		#Stop Slave.sender
		header 	= HEADER_SENDER_STOP
		args 	= None
		self.producer.add_task_fanout( serialize( (header, args) ) , exchange="artemis_monitor_slave_out")
		sleep(1)
		 
		#Start new netarea
		for master in masters:
			header 	= HEADER_NETAREA_PROPAGATION
			args 	= (master, net_tree)
			self.producer.add_task( serialize( (header, args) ) , exchange="artemis_monitor_master_out", routing_key=master.id  )
		sleep(1)
		
		#Start Slave.sender
		header 	= HEADER_SENDER_START
		args 	= net_tree
		self.producer.add_task_fanout( serialize( (header, args) ) , exchange="artemis_monitor_slave_out")
		
	def run(self):
		logging.debug("Monitor started")
		
		for w in self.in_pool:
			w.start()
			
		self.slave_out.start()
		while True:
			self.detect()
			self.balance()
			sleep(1)
