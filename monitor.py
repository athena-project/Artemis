# coding: utf-8
import configparser
import logging
import sys
import json

from artemis.Monitor import Monitor
from artemis.network.Reports import MonitorReport


debug = True

config = configparser.ConfigParser()
config.optionxform=str
config.read('/usr/local/conf/artemis/monitor.ini')

monitors_map = json.load( open('/usr/local/conf/artemis/monitors.json', 'r') )
monitors = {}
for _host, _port in monitors_map.items():
	monitors[(_host, _port)] = MonitorReport(_host, int(_port) ) 

if debug :
	logging.basicConfig( 
		stream= sys.stdout,
		format='%(asctime)s  %(levelname)s  %(filename)s %(funcName)s %(lineno)d %(message)s',
		level=logging.DEBUG)
else:
	logging.basicConfig(filename=config['Logger']['dir']+"/monitor-error.log", 
		format='%(asctime)s  %(levelname)s  %(filename)s %(funcName)s %(lineno)d %(message)s',
		level=logging.INFO)

monitor = Monitor(
	host			= config['General']['host'],
	monitors		= monitors,
	port			= 1984,
	limitFreeMasters= int(config['General']['limitFreeMasters'])
)
monitor.run()
