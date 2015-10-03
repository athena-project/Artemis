# coding: utf-8
import configparser
import logging

from artemis.Monitor import * 

config = configparser.ConfigParser()
config.read('conf/monitor.ini')

logging.basicConfig(filename=config['Logger']['dir']+"/monitor-error.log", 
	format='%(asctime)s  %(levelname)s  %(filename)s %(funcName)s %(lineno)d %(message)s',
	level=logging.DEBUG)

def configDict2boolDict(cDict):
	d={}
	for key in cDict:
		d[key]=cDict.getboolean(key)
	return d

monitor = Monitor(
	in_monitors		= int(config['General']['in_monitors']),
	limitFreeMasters= int(config['General']['limitFreeMasters'])
)
monitor.run()
