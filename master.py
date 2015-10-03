# coding: utf-8
import configparser
import logging

from artemis.Master import * 
from artemis.Task import Task, TASK_WEB_STATIC_TOR
from artemis.Netarea import *
from artemis.network.AMQPProducer import AMQPProducer
from artemis.Utility import serialize

config = configparser.ConfigParser()
config.read('conf/master.ini')

logging.basicConfig(filename=config['Logger']['dir']+"/master-error.log", 
	format='%(asctime)s  %(levelname)s  %(filename)s %(funcName)s %(lineno)d %(message)s',
	level=logging.DEBUG)

def configDict2boolDict(cDict):
	d={}
	for key in cDict:
		d[key]=cDict.getboolean(key)
	return d

master = Master(
	id				= config['General']['id'],
	useragent		= config['General']['useragent'],
	domainRules		= configDict2boolDict( config['DomainRules'] ),
	protocolRules	= configDict2boolDict( config['ProtocolRules'] ),
	originRules		= configDict2boolDict( config['OriginRules'] ),
	delay 			= int( config['Update']['delay'] ),
	maxNumNetareas	= int( config['Netarea']['maxNumNetareas'] ),
	maxRamNetarea	= int( config['Netarea']['maxRamNetarea'] )
)

p=AMQPProducer("artemis_master_out")
for url in config['Http_gateway'] :
	p.add_task( serialize([Task("http://"+url)]))
#p.add_task( serialize([Task("http://xmh57jrzrnw6insl.onion", nature=TASK_WEB_STATIC_TOR)]))
#p.add_task( serialize([Task("ftp://debian.org")]))
#p=AMQPProducer("artemis_master_out_torrent")
#p.add_task( serialize([Task("magnet:?xt=urn:btih:859da4d7affd6efd937236edfb19c5ff1cb51f0a&dn=ubuntu-12.04.5-server-amd64.iso", nature=TASK_WEB_STATIC_TORRENT)]))
#p.add_task( serialize([Task("magnet:?xt=urn:btih:bc84cb84010074094dba7bb55eebf68c6b3934a2&dn=debian-8.2.0-amd64-CD-1.iso", nature=TASK_WEB_STATIC_TORRENT, is_dir=True)]))
	#print(url)

master.harness()
