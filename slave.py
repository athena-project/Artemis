import configparser
import json
import logging
import sys
from collections import defaultdict
from artemis.Slave import Slave
from artemis.network.Reports import MonitorReport
debug = True

config = configparser.ConfigParser()
config.optionxform=str
config.read('/usr/local/conf/artemis/slave.ini')

monitors_map = json.load( open('/usr/local/conf/artemis/monitors.json', 'r') )
monitors = {}
for _host, _port in monitors_map.items():
	monitors[(_host, _port)] = MonitorReport(_host, int(_port) ) 

if debug :
	logging.basicConfig(
		stream=sys.stdout,
		format='%(asctime)s  %(levelname)s  %(filename)s %(funcName)s %(lineno)d %(message)s',
		level=logging.DEBUG)
else:
	logging.basicConfig(filename=config['Logger']['dir']+"/slave-error.log", 
		format='%(asctime)s  %(levelname)s  %(filename)s %(funcName)s %(lineno)d %(message)s',
		level=logging.INFO)

def configDict2boolDict(cDict):
	d=defaultdict( lambda : cDict.getboolean("*") )
	for key in cDict:
		d[key]=cDict.getboolean(key)
	return d

s=Slave(
	host					= config['General']['host'],
	monitors				= monitors,
	serverNumber			= int( config['General']['serverNumber'] ), 
	useragent				= config['General']['useragent'], 
	maxCrawlers				= int( config['Thread']['maxCrawlers'] ),  
	maxWorkers				= int( config['Thread']['maxWorkers'] ),  
	delay					= int( config['General']['delay'] ),
	dfs_path				= config['Storage']['dfs_path'],
	contentTypes			= configDict2boolDict( config['ContentTypes'] ),
	domainRules				= configDict2boolDict( config['DomainRules'] ),
	protocolRules			= configDict2boolDict( config['ProtocolRules'] ),
	originRules				= configDict2boolDict( config['OriginRules'] ),
	maxTasks				= int( config['Memory']['maxTasks'] ), 
	maxTorrents				= int( config['Memory']['maxTorrents'] ), 
	maxNewTasks				= int( config['Memory']['maxNewTasks'] ), 
	maxDoneTasks			= int( config['Memory']['maxDoneTasks'] ),  
	maxRessources			= int( config['Memory']['maxRessources'] ), 
	maxSavedRessources		= int( config['Memory']['maxSavedRessources']),
	maxActiveTorrents		= int( config['General']['maxActiveTorrents'] )
)


#from artemis.Task import *
#s.pool[0].newTasks.append( Task("http://fr.wikipedia.org") )

#Task("http://xmh57jrzrnw6insl.onion", nature=TASK_WEB_STATIC_TOR)
#Task("ftp://debian.org")
#Task("magnet:?xt=urn:btih:859da4d7affd6efd937236edfb19c5ff1cb51f0a&dn=ubuntu-12.04.5-server-amd64.iso", nature=TASK_WEB_STATIC_TORRENT)
#serialize([Task("magnet:?xt=urn:btih:bc84cb84010074094dba7bb55eebf68c6b3934a2&dn=debian-8.2.0-amd64-CD-1.iso", nature=TASK_WEB_STATIC_TORRENT, is_dir=True)])

s.harness()

