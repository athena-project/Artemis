import configparser
import Slave
import Master
from threading import Thread, Event
import time
import SQLFactory
import RedisFactory
from math import *
import Url
import os
######################## STAT FRUNCTIONS ########################  
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
	d=duration(table)
	
	return (count(table)/duration(table)) if d != None else 0
	
########################  END ########################


import logging
logging.basicConfig(#filename="/var/log/artemis/error.log", 
					format='%(asctime)s  %(levelname)s  %(filename)s %(funcName)s %(message)s',
					level=logging.INFO)

########################  BEGIN CONFIG ########################  
def configDict2boolDict(cDict):
	d={}
	for key in cDict:
		d[key]=cDict.getboolean(key)
	return d


config1 = configparser.ConfigParser()
config1.read('/etc/artemis/slave.ini')

config2 = configparser.ConfigParser()
config2.read('/etc/artemis/master.ini')

########################  END ########################  

con = SQLFactory.getConn()
redis = RedisFactory.getConn()






#class s(Process):
	#def __init__(self, m):
		#Process.__init__(self)
		#self.m=m
		#self.s = None
	#def __del__(self):
		#del self.s
		#pass
	#def run(self):
		#self.s=Slave.Slave(
			#useragent		= config1['General']['useragent'],  
			#period			= int( config1['General']['period'] ), 
			#maxWorkers		= int( config1['Thread']['maxWorkers'] ),
			#contentTypes	= configDict2boolDict( config1['ContentTypes'] ), 
			#delay			= int( config1['Update']['delay'] ),
			#maxCrawlers		= self.m,
			#sqlNumber		= int( config1['SQL']['number'] ),
			#maxNewUrls		= int( config1['General']['maxNewUrls'] )
		#)

		#self.s.start()

#class m(Process):
	#def __init__(self):
		#Process.__init__(self)
		#self.master = None
		
	#def __del__(self):
		#del self.master
		
	#def run(self):
		#self.master = Master.Master(
			#serverNumber	= int(config2['General']['serverNumber']), 
			#useragent		= config2['General']['useragent'], 
			#period			= int( config2['General']['period'] ), 
			#domainRules		= configDict2boolDict( config2['DomainRules'] ),
			#protocolRules	= configDict2boolDict( config2['ProtocolRules'] ),
			#originRules		= configDict2boolDict( config2['OriginRules'] ),
			#delay 			= int( config2['Update']['delay'] ),
			#maxRamSize		= int( config2['UrlHandling']['maxRamSize'] ),
			#gateway			= config2['Gateway']
		#)
		#self.master.start()

class SlaveTest(Thread, Slave.Slave ):
	def __init__(self, serverNumber=1, useragent="*", period=10, maxWorkers=2, contentTypes={"*":False},
		delay=86400, maxCrawlers=1, sqlNumber=100, maxNewUrls=10000, Exit=None) :
			
		Thread.__init__(self)
		self.daemon			= True
		self.pool			= []
		self.serverNumber 	= serverNumber
		self.Exit			= Exit
		
		for i in range(0, self.serverNumber):
			s = Slave.Server(useragent, period, maxWorkers, contentTypes, delay, maxCrawlers, sqlNumber, maxNewUrls)
			self.pool.append( s )
			
		logging.info("Servers started")
	
	def run(self):
		for server in self.pool:
			server.start()
		
		while not self.Exit.is_set():
			time.sleep( 1 )

class MasterTest(Thread, Master.Master):
	def __init__(self, serverNumber=1, useragent="*", period=10, domainRules={"*":False},
				protocolRules={"*":False}, originRules={"*":False}, delay = 36000,
				maxRamSize=100, gateway=[], Exit=None):
		
		Thread.__init__(self)
		self.pool			= []
		self.serverNumber 	= serverNumber
		self.Exit			= Exit
		
		for i in range(0, self.serverNumber):
			s = Master.Server(useragent, period, domainRules, protocolRules, originRules, delay, maxRamSize)
			self.pool.append( s )
			
		for url in gateway:
				self.pool[0].urlCacheHandler.add( Url.Url(url="http://"+url) ) 
		logging.info("Servers started")
		
	def run(self):
		for server in self.pool:
			server.start()
		
		while not self.Exit.is_set():
			time.sleep( 1 )

n=2
def test_load( n, timesleep ):
	loads = []
	for k in range(1, n):
		
		print("begin")
		truncate("html")
		redis.flushall()
		Exit=Event()
		p = SlaveTest(
				serverNumber	= int(config2['General']['serverNumber']), 
				useragent		= config1['General']['useragent'],  
				period			= int( config1['General']['period'] ), 
				maxWorkers		= int( config1['Thread']['maxWorkers'] ),
				contentTypes	= configDict2boolDict( config1['ContentTypes'] ), 
				delay			= int( config1['Update']['delay'] ),
				maxCrawlers		= k,
				sqlNumber		= int( config1['SQL']['number'] ),
				maxNewUrls		= int( config1['General']['maxNewUrls'] ),
				Exit			= Exit
		)
		q = MasterTest(
				serverNumber	= int(config2['General']['serverNumber']), 
				useragent		= config2['General']['useragent'], 
				period			= int( config2['General']['period'] ), 
				domainRules		= configDict2boolDict( config2['DomainRules'] ),
				protocolRules	= configDict2boolDict( config2['ProtocolRules'] ),
				originRules		= configDict2boolDict( config2['OriginRules'] ),
				delay 			= int( config2['Update']['delay'] ),
				maxRamSize		= int( config2['UrlHandling']['maxRamSize'] ),
				gateway			= config2['Gateway'],
				Exit			= Exit
		)
		q.start()
		p.start()
		time.sleep(timesleep)
		Exit.set()
		#print(k, "   ", speed("html"))
		f= open("results"+str(timesleep)+"-"+str(k), "a")
		f.write(str(k)+";"+str(speed("html"))+";")
		f.close()
		
		loads.append( speed("html") )
		time.sleep(2)
		del p
		del q
		os.system("killall -9 beam.smp")
		os.system("invoke-rc.d rabbitmq-server start")
		truncate("html")
		redis.flushall()
		time.sleep(2)
	return loads


l=test_load( 20, 300 ) 
