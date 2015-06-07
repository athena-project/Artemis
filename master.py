# coding: utf-8
import configparser
import logging
#import Url
from src.Master import * 
from src.Netarea import *

logging.basicConfig(filename="master-error.log", 
	format='%(asctime)s  %(levelname)s  %(filename)s %(funcName)s %(lineno)d %(message)s',
	level=logging.DEBUG)

def configDict2boolDict(cDict):
	d={}
	for key in cDict:
		d[key]=cDict.getboolean(key)
	return d


config = configparser.ConfigParser()
config.read('conf/master.ini')


master = Master(
	netareas		= [NetareaReport("00000000000000000000000000000000",0, 1<<25, 1<<384)],
	ip				= config['General']['ip'],
	useragent		= config['General']['useragent'],
	domainRules		= configDict2boolDict( config['DomainRules'] ),
	protocolRules	= configDict2boolDict( config['ProtocolRules'] ),
	originRules		= configDict2boolDict( config['OriginRules'] ),
	delay 			= int( config['Update']['delay'] ),
	maxNumNetareas	= int( config['Netarea']['maxNumNetareas'] ),
	maxRamNetarea	= int( config['Netarea']['maxRamNetarea'] )
	#gateway			= config['Gateway']
)
#master.harness()
