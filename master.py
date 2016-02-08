# coding: utf-8
import configparser
import logging
import sys

from artemis.Master import Master

debug = True

config = configparser.ConfigParser()
config.optionxform=str
config.read('/usr/local/conf/master.ini')

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
	monitors		= [('127.0.1.1', 1984)],
	useragent		= config['General']['useragent'],
	delay 			= int( config['Update']['delay'] ),
	maxNumNetareas	= int( config['Netarea']['maxNumNetareas'] ),
	maxRamNetarea	= int( config['Netarea']['maxRamNetarea'] )
)

master.harness()
