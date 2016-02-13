import artemis.Utility as utility
from enum import IntEnum

class MsgType(IntEnum):
	NOTHING								= 0

	ANNOUNCE_SLAVE						= 0x1 # un esclave se declare aux moniteurs
	ANNOUNCE_MASTER						= 0x2 # un maitre se declare aux moniteurs
	ANNOUNCE_SLAVE_MAP					= 0x3 # le moniteur leader declare les esclaves à tous les maitres
	ANNOUNCE_DELTA_SLAVE_MAP			= 0x31# le moniteur leader declare les modifications de la map des esclaves à tous les maitres
	
	ANNOUNCE_NET_TREE					= 0x4 # le moniteur leader declare les maitres à tous les esclaves
	ANNOUNCE_DELTA_NET_TREE				= 0x41# le moniteur leader declare les maitres à tous les esclaves
	ANNOUNCE_NET_TREE_UPDATE_INCOMING	= 0x5 # le moniteur leader déclare aux esclaves qu'il va y avoir une maj
	ANNOUNCE_NET_TREE_PROPAGATE			= 0x51# le moniteur leader déclare aux esclaves que les modifications
	ANNOUNCE_NETAREA_UPDATE				= 0x6 # le moniteur leader déclare les neatareas à managé aux serveuurs maitres
	
	MASTER_IN_TASKS						= 0x7 # tasks from slave to master
	MASTER_DONE_TASKS					= 0x8 # tasks from slave to master
	SLAVE_IN_TASKS						= 0x9 # tasks from master to slave
	MONITOR_HEARTBEAT					= 0xa
	
	ANNOUNCE_MONITORS					= 0xb # only by leader
	ANNOUNCE_DELTA_MONITORS				= 0xb1# only by leader
	
	metric_expected						= 0xc # demande de statistique à la cible, obj : (host, port) où répondre
	metric_monitor						= 0xd # communique la liste des esclaves, des maitres, des monitors, et le netree
	metric_netarea						= 0xe # communique le nombre d'url stockée dans ce noeuds
	metric_slave						= 0xf # communique une estimation de le nombre d'url traitée sur le dernier interval, et l'intervalle correspondant

class Msg:
	def __init__(self, t=MsgType.NOTHING, obj=None):
		self.t		= t 
		self.obj 	= obj
	
	def serialize(self):
		return utility.serialize( self )
	
	def __str__(self):
		return str(self.serialize())

	def pretty_str(self):
		return "Msg  type=%s obj=%s " % ( self.t, self.obj ) 
