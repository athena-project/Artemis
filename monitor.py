# coding: utf-8
import configparser
import logging
import sys

from artemis.Monitor import Monitor

debug = True

config = configparser.ConfigParser()
config.optionxform=str
config.read('/usr/local/conf/artemis/monitor.ini')

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
	monitors		= [('138.231.140.228', 1984)],
	port			= 1984,
	limitFreeMasters= int(config['General']['limitFreeMasters'])
)
monitor.run()
