import configparser
import Slave
import Master
from multiprocessing import Process
import time
import SQLFactory
import RedisFactory
from math import *

import logging
logging.basicConfig(filename="/var/log/artemis/error.log", format='%(asctime)s  %(levelname)s  %(message)s',
	level=logging.DEBUG)

def configDict2boolDict(cDict):
	d={}
	for key in cDict:
		d[key]=cDict.getboolean(key)
	return d


config1 = configparser.ConfigParser()
config1.read('/etc/artemis/slave.ini')

config2 = configparser.ConfigParser()
config2.read('/etc/artemis/master.ini')



con = SQLFactory.getConn()
redis = RedisFactory.getConn()




def truncate(table):
	cur = con.cursor()
	cur.execute('TRUNCATE '+table )
	cur.close()

def duration(table):
	duration = -1
	cur = con.cursor()
	cur.execute('SELECT MAX(lastUpdate) - MIN(lastUpdate) AS duration FROM '+table)
	
	for row in cur: #url is a unique id
		duration = row[0]
	cur.close()
	return duration
	
def count(table):
	count = -1
	cur = con.cursor()
	cur.execute('SELECT COUNT(id) AS c FROM '+table)
	
	for row in cur: #url is a unique id
		count = row[0]
	cur.close()
	return count



def speed(table):
	return count(table)/duration(table)

class s(Process):
	def __init__(self, m):
		Process.__init__(self)
		self.m=m
		self.s = None
	def __del__(self):
		#del self.s
		pass
	def run(self):
		self.s=Slave.Slave(
			useragent		= config1['General']['useragent'],  
			period			= int( config1['General']['period'] ), 
			maxWorkers		= int( config1['Thread']['maxWorkers'] ),
			contentTypes	= configDict2boolDict( config1['ContentTypes'] ), 
			delay			= int( config1['Update']['delay'] ),
			maxCrawlers		= self.m,
			sqlNumber		= int( config1['SQL']['number'] ),
			maxNewUrls		= int( config1['General']['maxNewUrls'] )
		)

		self.s.harness()

class m(Process):
	def __init__(self):
		Process.__init__(self)
		self.master = None
		
	def __del__(self):
		if self.master != None:
			self.master.terminate()
		
	def run(self):
		self.master = Master.Master(
			serverNumber	= int(config2['General']['serverNumber']), 
			useragent		= config2['General']['useragent'], 
			period			= int( config2['General']['period'] ), 
			domainRules		= configDict2boolDict( config2['DomainRules'] ),
			protocolRules	= configDict2boolDict( config2['ProtocolRules'] ),
			originRules		= configDict2boolDict( config2['OriginRules'] ),
			delay 			= int( config2['Update']['delay'] ),
			maxRamSize		= int( config2['UrlHandling']['maxRamSize'] ),
			gateway			= config2['Gateway']
		)
		self.master.start()

n=16
for k in range(1, n):
	truncate("html")
	redis.flushall()
	p = s(k)
	q = m()
	q.start()
	p.start()
	time.sleep(20)
	p.terminate()
	q.terminate()
	print(k, "   ", speed("html"))
	truncate("html")
	redis.flushall()
