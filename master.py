# coding: utf-8
import configparser
import logging
import sys
import json

from artemis.Master import Master
from artemis.network.Reports import MonitorReport

debug = True

config = configparser.ConfigParser()
config.optionxform=str
config.read('/usr/local/conf/artemis/master.ini')

monitors_map = json.load( open('/usr/local/conf/artemis/monitors.json', 'r') )
monitors = {}
for _host, _port in monitors_map.items():
	monitors[(_host, _port)] = MonitorReport(_host, int(_port) ) 

if debug :
	logging.basicConfig(
		stream= sys.stdout,
		format='%(asctime)s  %(levelname)s  %(filename)s %(funcName)s %(lineno)d %(message)s',
		level=logging.DEBUG)
else :
	logging.basicConfig(filename=config['Logger']['dir']+"/master-error.log", 
		format='%(asctime)s  %(levelname)s  %(filename)s %(funcName)s %(lineno)d %(message)s',
		level=logging.INFO)
	

master = Master(
	host 			= config['General']['host'],
	monitors		= monitors,
	useragent		= config['General']['useragent'],
	delay 			= int( config['Update']['delay'] ),
	maxNumNetareas	= int( config['Netarea']['maxNumNetareas'] ),
	maxRamNetarea	= int( config['Netarea']['maxRamNetarea'] )
)

master.harness()
