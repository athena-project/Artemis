from .network.TcpClient import TcpClient
from .network.Msg import Msg, MsgType
from .network.TcpServer import P_TcpServer, T_TcpServer, TcpServer
from .network.Reports	import NetareaReport, MonitorReport

from .AVL import *

from time import sleep
from threading import Thread, RLock, Event
from multiprocessing import Process, Queue
from .Utility import serialize, unserialize
from copy import deepcopy
from math import ceil, floor
from .Netarea import NetareaTree, MAX as NETAREA_MAX
from enum import IntEnum
import logging
from collections import defaultdict

import traceback, sys
from blist import sortedlist

debug=True

FIRST_RATE			= 0.5 #proportion de netarea alloué la première fois

#Constantes used in Leader election
class Status(IntEnum):
	passive		= 0
	dummy		= 1	
	waiting		= 2
	candidate 	= 3
	leader		= 4
	
class Action(IntEnum): #msg.type
	ALG			= 0
	AVS			= 1
	AVSRP		= 2
	
class LogicalNode: # in a logical ring
	def __init__(self, host, port, monitors):
		"""
			monitors [ (host, port)]
		"""
		self.identity	= hash( (host, port) )
		self.host		= host
		self.port		= port
		self.status		= Status.candidate
		self.succ 		= self.get_succ(monitors) # <=>neighi
		self.cand_pred	= None #logical node
		self.cand_succ	= None #same
		
	def get_succ(self, monitors):
		tmp 			= monitors[ (self.host, self.port) ]
		tmp_monitors	= list(monitors.values())
		tmp_monitors.sort( 
			key=(lambda item : hash( (item.host, item.port) ) ) )
		
		i = tmp_monitors.index(tmp)
		
		if i != len(tmp_monitors)-1:
			return tmp_monitors[i+1]
		else :
			return tmp_monitors[0]		
		 
	def __ge__(self, node):#self>=
		return self.identity>=node.identity
	
	def __gt__(self, node):#self>
		return self.identity>node.identity
		
	def __le__(self, node):#self<=
		return self.identity<=node.identity
	
	def __lt__(self, node):#self<
		return self.identity<node.identity
		
	def __ne__(self, node):#self!=
		return self.identity!=node.identity
	
	def __eq__(self, node):
		return self.identity == node.identity
		
class MonServer(T_TcpServer):
	def __init__(self, host, port, monitors, delta_monitors, ev_leader, 
		masterReports, slaveReports, delta_slaves, netTree, Exit, 
		monitors_lock, masters_lock, slaves_lock, delta_slaves_lock, 
		netTree_lock, Propagate):

		self.port			= port
		self.monitors		= monitors
		self.delta_monitors	= delta_monitors
		self.ev_leader		= ev_leader #to announce if it's the leader to Monitor
		
		T_TcpServer.__init__(self, host, Exit)
		
		self.client			= TcpClient()
		
		self.masterReports	= masterReports
		self.slaveReports	= slaveReports
		self.delta_slaves	= delta_slaves
		self.netTree		= netTree
		
		self.monitors_lock	= monitors_lock
		self.masters_lock	= masters_lock
		self.slaves_lock	= slaves_lock
		self.delta_slaves_lock	= delta_slaves_lock
		self.netTree_lock	= netTree_lock
				
		self.Propagate		= Propagate
		
		#Attributs used in Leader election : see  J. Villadangos, A. Cordoba, F. Farina, and M. Prieto, 2005, "Efficient leader election in complete networks"
		self.node 			= LogicalNode( self.get_host(), 
			port, monitors)
		self.client.send( Msg( Action.ALG, (self.node, self.node) ), 
			self.node.succ.host, self.node.succ.port)
		
	def find_port(self):#ON FORCE LE PORT
		self.bind()
		
	def callback(self, data):
		msg	= TcpServer.callback(self, data)
				
		if msg.t == MsgType.ANNOUNCE_SLAVE :
			if( self.ev_leader.is_set() 
			and not self.Propagate.is_set()
			and not msg.obj.id() in self.slaveReports):
				with self.netTree_lock:
					self.client.send( 
						Msg(MsgType.ANNOUNCE_NET_TREE, self.netTree), 
						msg.obj.host, msg.obj.port)
			
			with self.delta_slaves_lock:	
				self.delta_slaves[0].append( msg.obj )
				
			with self.slaves_lock:
				self.slaveReports[ msg.obj.id() ] = msg.obj
				
		elif msg.t == MsgType.ANNOUNCE_MASTER:
			if self.ev_leader.is_set():
				with self.slaves_lock:
					for report in msg.obj.netarea_reports:
						self.client.send( 
							Msg(MsgType.ANNOUNCE_SLAVE_MAP, 
							self.slaveReports), 
							report.host, report.port)
				
			with self.masters_lock:
				self.masterReports[ msg.obj.id() ] = msg.obj
		elif msg.t == MsgType.MONITOR_HEARTBEAT:
			with self.monitors_lock:
				if not msg.obj in self.monitors:
					self.delta_monitors[0].append( msg.obj )
				self.monitors[ msg.obj.id() ] = msg.obj
					
			with self.netTree_lock:
				self.client.send( 
					Msg(MsgType.ANNOUNCE_NET_TREE, self.netTree), 
					msg.obj.host, msg.obj.port)
		elif msg.t == MsgType.ANNOUNCE_DELTA_NET_TREE:
			if not self.ev_leader.is_set():
				with self.netTree_lock:
					for net in msg.obj[1]:
						self.netTree.suppr( net.netarea )

					for net in msg.obj[0]:
						self.netTree[ net.netarea] = net
						
					for net in msg.obj[2]:
						self.netTree[ net.netarea ].next_netarea= net.next_netarea
						self.netTree[ net.netarea ].used_ram 	= net.used_ram 
		elif msg.t == MsgType.ANNOUNCE_NET_TREE:
			if not self.ev_leader.is_set():
				with self.netTree_lock:
					self.netTree.update( msg.obj )
		elif msg.t == MsgType.metric_expected:
			host, port = msg.obj
			with self.monitors_lock, self.masters_lock, self.slaves_lock, self.netTree_lock:
				self.client.send( Msg(MsgType.metric_monitor, 
					[self.monitors, self.slaveReports, self.masterReports,
						self.netTree]
					), host, port)
		elif msg.t == Action.ALG :
			i		= self.node
			init,j  = msg.obj #i<-j avec data = init

			if i.status == Status.passive: #msg.obj is a logicalNode
				i.status	= Status.dummy
				self.client.send( Msg( Action.ALG, (init, i) ), 
					i.succ.host, i.succ.port)
			elif i.status == Status.candidate:
				i.cand_pred	= msg.obj
				if i > init:
					if i.cand_succ == None:
						i.status	= Status.waiting
						self.client.send( Msg( Action.AVS, i), 
							init.host, init.port)
					else:
						i.status	= Status.dummy
						self.client.send( 
							Msg( Action.AVSRP, (i.cand_pred,i)), 
							i.cand_succ.host, i.cand_succ.port)

				elif i == init:
					i.status	= Status.leader
					self.ev_leader.set()
		elif msg.t == Action.AVS :
			i,j= self.node, msg.obj
			
			if i.status == Status.candidate :
				if i.cand_pred == None :
					i.cand_succ = j
				else:
					i.status	= Status.dummy
					self.client.send( Msg( Action.AVSRP, i.cand_pred), 
						j.host, j.port)
			elif self.node.status	== Status.waiting:
				self.cand_succ	= j 
		elif msg.t == Action.AVSRP : 
			i	= self.node
			k,j	= msg.obj #k data, j sender
			if i.status == Status.waiting :
				if i == k :
					i.status	= Status.leader
					self.ev_leader.set()
				else:
					i.cand_pred	= k
					if i.cand_succ == None :
						if k<i:
							i.status	= Status.waiting
							self.client.send( Msg(Action.AVS, i), 
								k.host, k.port)
					else:
						i.status	= Status.dummy
						self.client.send( Msg(Action.AVSRP, (k,i)), 
							i.cand_succ.host, i.cand_succ.port )
		else:
			logging.info("Unknow received msg %s" % msg.pretty_str())

class MasterOut(Thread):
	def __init__(self, host, port, monitors, delta_monitors, Leader, 
		masterReports, slaveReports,  delta_slaves, Exit, monitors_lock, 
		masters_lock, slaves_lock, delta_slaves_lock):
		Thread.__init__(self)
		
		self.host				= host
		self.port				= port
		self.monitors			= monitors
		self.delta_monitors		= delta_monitors
		self.slaveReports		= slaveReports
		self.delta_slaves		= delta_slaves
		self.masterReports		= masterReports
		self.Leader				= Leader
		self.Exit				= Exit
		self.monitors_lock		= monitors_lock
		self.masters_lock		= masters_lock
		self.slaves_lock		= slaves_lock
		self.delta_slaves_lock	= delta_slaves_lock
		
		self.client = TcpClient()

	
	def run(self):
		while not self.Exit.is_set():
			if self.Leader.is_set():
				with self.monitors_lock:
					flag2 = ( self.delta_monitors[0] == [] and self.delta_monitors[1] == [] )
					if not flag2:
						msg2 = Msg(MsgType.ANNOUNCE_MONITORS, deepcopy(self.delta_monitors))
						self.delta_monitors[0].clear()
						self.delta_monitors[1].clear()
					
				with self.slaves_lock and self.delta_slaves_lock:
					flag1 = ( self.delta_slaves[0] == [] and self.delta_slaves[1] == [] )
					if not flag1:
						msg1 = Msg(MsgType.ANNOUNCE_DELTA_SLAVE_MAP, 
							self.delta_slaves)
					
					if not flag2 and not flag:
						continue
						
					with self.masters_lock:
						for master in self.masterReports.values():
							if not flag2 :
								self.client.send( msg2, master.host, 
									master.port )
							
							if not flag1:
								for report in master.netarea_reports:
									self.client.send( msg1, report.host, 
										report.port )
							
						if not flag2 :	
							for report in self.slaveReports.values():
								self.client.send( msg2, report.host, 
									report.port )
					if not flag1:
						self.delta_slaves[0].clear()
						self.delta_slaves[1].clear()

			#heartbeat
			with self.monitors_lock:
				for m_host, m_port in self.monitors :
					if m_host != self.host:
						self.client.send( Msg(MsgType.MONITOR_HEARTBEAT, 
						MonitorReport(self.host, self.port)), m_host, m_port )
					else:
						self.monitors[ (self.host, self.port) ].reset() 
			sleep(1)
					
class Monitor(Thread):
	def __init__(self, host, port, monitors, limitFreeMasters):
		"""
			@param limitFreeMasters - minimum number of master which are not overload in the cluster
		"""
		self.monitors			= monitors
		self.delta_monitors		= ([], []) #first list : addition, second : deletion 
		self.limitFreeMasters 	= limitFreeMasters
		self.Exit 				= Event()
		self.Leader 			= Event()
		self.Propagate 			= Event()
		
		self.masterReports 		= {} #received reports from masters
		self.slaveReports 		= {} 
		self.delta_slaves		= ([], []) #first list : addition, second : deletion
		self.netTree			= NetareaTree()
		self.delta_netareas		= (defaultdict(list), defaultdict(list), defaultdict(list)) #first list : addition, second : deletion [0][masters]=[netareas]

		self.monitors_lock		= RLock()
		self.masters_lock		= RLock()
		self.slaves_lock		= RLock()
		self.delta_slaves_lock	= RLock()
		self.netTree_lock		= RLock()
		self.server				= MonServer( 
			host, 
			port,
			self.monitors,
			self.delta_monitors, 
			self.Leader,
			self.masterReports,
			self.slaveReports,
			self.delta_slaves,
			self.netTree,
			self.Exit,
			self.monitors_lock,
			self.masters_lock,
			self.slaves_lock,
			self.delta_slaves_lock,
			self.netTree_lock, 
			self.Propagate)
		self.host				= self.server.get_host()
		self.port				= port
		self.masterOut			= MasterOut( self.host,
			self.port,
			self.monitors,
			self.delta_monitors, 
			self.Leader, 
			self.masterReports, 
			self.slaveReports, 
			self.delta_slaves, 
			self.Exit,
			self.monitors_lock,
			self.masters_lock,
			self.slaves_lock,
			self.delta_slaves_lock)

		self.client 			= TcpClient()
		logging.debug("Monitor initialized")
		
	def terminate(self):
		self.Exit.set()
		logging.info("Monitor stoped")

	def is_overload(self, masters):
		for report in masters:
			for netarea in report.netarea_reports:
				if netarea.is_overload():
					return True
		return False
		
	def first_allocation(self, masters):		
		max_netareas = sum([r.maxNumNetareas for r in masters])
		if max_netareas == 0:
			return
		
		begin = 0
		step = ceil(NETAREA_MAX / int( FIRST_RATE * max_netareas ))
		last = None
				
				
		for m in masters:
			for i in range( floor(m.maxNumNetareas * FIRST_RATE) ): #floor needed otherwith some netarea will be above NETAREA_MAX
				net	= NetareaReport(m.host, -1, begin,0, 1<<25, 
						begin+step)
				self.delta_netareas[0][m].append( net )
				begin += step
				m.allocate( net )
				last = net
		
		if last : #due to ceil and floor
			last.next_netarea = NETAREA_MAX 
				
		self.propagate(masters)
			
	def allocate(self, masters, unallocated_netarea):
		"""
			assuming all masters are alive, ie call prune before
		"""
		if not masters:
			logging.critical( 
				"Masters must be added, system is overload")
			return None
		
		while( unallocated_netarea ):
			medium_load = float(sum([ m.load() for m in masters ])) / len( masters )
			under_loaded = sortedlist( [ m for m in masters if m.load() <= medium_load ] ) #<= for the first alloc : all load = 0
			if not under_loaded :
				under_loaded = [ m for m in masters if not m.is_overload() ]
				if not under_loaded :
					logging.critical( 
					"Masters must be added, system is overload")
					return None
					
			while( unallocated_netarea and under_loaded):		
				m, net = under_loaded.pop( 0 ), unallocated_netarea.pop()
				self.delta_netareas[0][m].append( net )
				m.allocate( net )
				
				if( m.load() < medium_load ):
					under_loaded.add( m )
			
		if( sum([ int(not master.is_overload()) 
			for master in masters ]) < self.limitFreeMasters):
			logging.warning( 
				"Masters should be added, system will be overload")
		
		self.propagate(masters)
		
	def prune(self):
		with self.masters_lock:
			del_key, unallocated_netarea = [], []
			for key, m in self.masterReports.items():
				if m.is_expired() :
					del_key.append( key )
					self.delta_netareas[1][m].extend( m.netarea_reports )
					unallocated_netarea.extend( m.netarea_reports )
					
			for key in del_key:
				del self.masterReports[key]
				
		if self.Leader.is_set() :
			masters = []
			with self.masters_lock:
				masters =  deepcopy( list(self.masterReports.values() ))
			if unallocated_netarea:
				with self.netTree_lock:
					for net in unallocated_netarea:
						self.netTree.suppr( net.netarea )
				self.allocate( masters, unallocated_netarea)	
				
				
		mon_flag	= False
		with self.monitors_lock :
			for key, monitor in list(self.monitors.items()):
				if monitor.is_expired():
					self.delta_monitors[1].append( monitor )
					del self.monitors[ key ]
					mon_flag = True
			
			if mon_flag and not self.Leader.is_set() :
				tmp_node = LogicalNode(self.host, self.port, 
					self.monitors)
				self.client.send( Msg(Action.ALG, (tmp_node, tmp_node)), 
					tmp_node.succ.host, tmp_node.succ.port)
					

		with self.slaves_lock and self.delta_slaves_lock:
			for key, slave in list(self.slaveReports.items()):
				if slave.is_expired():
					logging.debug( slave )
					self.delta_slaves[1].append( slave ) 
					del self.slaveReports[ key ]
			
	def buildNetTreeFromScratch(self):
		with self.netTree_lock and self.masters_lock: 
			for master in self.masterReports.values():
				for netarea in master.netarea_reports:
					self.netTree[netarea.netarea] = netarea
						
	def balance(self):
		with self.masters_lock:
			masters =  deepcopy( list(self.masterReports.values() ))
			
		if sum([ len(r.netarea_reports) for r in self.masterReports.values() ]) == 0:
			self.first_allocation( masters )#No netarea allocated
			return 
		
		if not self.is_overload( masters ):
			with self.netTree_lock: 
				flag = self.netTree.empty()
			if flag:
				self.buildNetTreeFromScratch()

			return 
		unallocated_netarea	= []

		for master in masters:
			for netarea in master.netarea_reports:
				if netarea.is_overload():
					net1	= netarea.split()
					self.delta_netarea[2][master].append(netarea)					

					unallocated_netarea.append(net1)
		
		self.allocate( masters, unallocated_netarea)		
		return masters
		
	def propagate(self, masters):
		self.Propagate.set()

		net_tree = NetareaTree()
		for master in masters:
			for netarea in master.netarea_reports:
				net_tree[netarea.netarea]=netarea
				
		
		#Stop Slave.sender
		with self.slaves_lock:
			for slave in self.slaveReports.values():
				self.client.send( 
					Msg(MsgType.ANNOUNCE_NET_TREE_UPDATE_INCOMING, None), 
					slave.host, slave.port)
		sleep(2)
		 
		#Start new netarea
		#on suppose que l'on a pas besoin d'arreter les netareas : le master les hebergeant est perdu...?
		#verification quand on recupère un rappport pour netarea..
		updated_masters = {} # de liste
		for master, nets in self.delta_netareas[0].items():
			updated_masters[master]=[ nets, [] ]
			
		for master, nets in self.delta_netareas[2].items():
			if master in updated_masters:
				updated_masters[master][1] = nets 
			else:
				updated_masters[master]=[ [], nets ]

			
		for master, u_nets in updated_masters.items():
			self.client.send( 
				Msg(MsgType.ANNOUNCE_NETAREA_UPDATE, u_nets), 
				master.host, master.port)
				
		sleep(2)#master envoi la reponse toutes les secondes s'il ne répond pas tampis
		with self.masters_lock:
			for k in self.masterReports:
				print(self.masterReports[k])
		
		with self.netTree_lock: 
			self.netTree.update( net_tree )
			
			with self.masters_lock: 
				for master in self.masterReports.values():
					for netarea in master.netarea_reports:
						try:
							self.netTree.update_netarea(netarea) # faut recup port de netarea notament
						except Exception as e:
							logging.debug( "%s %s" % (
								traceback.extract_tb(sys.exc_info()[2]),
								str(e)))
			
		#Start Slave.sender
		deltas = ([],[],[])
		for k in range(3):
			for nets in self.delta_netareas[k].values():
				deltas[k].extend( nets )
				
		with self.slaves_lock :
			for slave in self.slaveReports.values():		
				self.client.send( 
					Msg(MsgType.ANNOUNCE_NET_TREE_PROPAGATE, deltas ), 
					slave.host, slave.port)
		
		with self.monitors_lock:
			for m_host, m_port in self.monitors :
				self.client.send( Msg(MsgType.ANNOUNCE_DELTA_NET_TREE, 
				deltas), m_host, m_port )
		
		self.Propagate.clear()
		self.delta_netareas[0].clear()
		self.delta_netareas[1].clear()
		self.delta_netareas[2].clear()
		logging.debug("Propagate, done")
		
	def run(self):	
		self.server.start()
		self.masterOut.start()
		
		r = range( 10 if debug else 600)
			
		while True:
			for k in r:
				self.prune()
				sleep(0.1)
				
			if self.Leader.is_set():
				self.balance()
				
			sleep(1)
