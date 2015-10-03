import configparser
import logging

from artemis.Slave import *

config = configparser.ConfigParser()
config.read('conf/slave.ini')

logging.basicConfig(filename=config['Logger']['dir']+"/slave-error.log", 
	format='%(asctime)s  %(levelname)s  %(filename)s %(funcName)s %(lineno)d %(message)s',
	level=logging.DEBUG)

def configDict2boolDict(cDict):
	d={}
	for key in cDict:
		d[key]=cDict.getboolean(key)
	return d

s=Slave(
	serverNumber				= int( config['General']['serverNumber'] ), 
	useragent					= config['General']['useragent'], 
	maxCrawlers					= int( config['Thread']['maxCrawlers'] ),  
	maxWorkers					= int( config['Thread']['maxWorkers'] ),  
	delay						= int( config['General']['delay'] ),
	sqlNumber					= int( config['DB']['sqlNumber'] ),
	dfs_path					= config['Storage']['dfs_path'],
	contentTypes				= configDict2boolDict( config['ContentTypes'] ),
	domainRules					= configDict2boolDict( config['DomainRules'] ),
	protocolRules				= configDict2boolDict( config['ProtocolRules'] ),
	originRules					= configDict2boolDict( config['OriginRules'] ),
	maxTasksSize				= int( config['Memory']['maxTasksSize'] ), 
	maxTorrentsSize				= int( config['Memory']['maxTorrentsSize'] ), 
	maxNewTasksSize				= int( config['Memory']['maxNewTasksSize'] ), 
	maxDoneTasksSize			= int( config['Memory']['maxDoneTasksSize'] ),  
	maxNewFormsSize				= int( config['Memory']['maxNewFormsSize'] ),  
	maxUnorderedRessourcesSize	= int( config['Memory']['maxUnorderedRessourcesSize'] ), 
	maxOrderedRessourcesSize	= int( config['Memory']['maxOrderedRessourcesSize'] ),  
	maxSavedRessourcesSize		= int( config['Memory']['maxSavedRessourcesSize']),
	maxActiveTorrents		= int( config['General']['maxActiveTorrents'] )
)
s.harness()

