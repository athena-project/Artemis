from urllib.parse import urlparse

import SQLFactory
import RedisFactory
import hashlib
from collections import deque

import pickle

	
class SQLUrlRecord:
	def __init__(self, urlRecord, ressource):
		self.urlRecord 	= urlRecord
		self.ressource	= ressource


class SQLUrlManager:
	def __init__(self, conn=None):
		self.conn = conn if conn != None else SQLFactory.getConn()
	
	def save(self, records):
		"""
			@param records	- list of SQLUrlRecord
		"""
		buff = ""
		for record in records:
			if buff != "":
				buff+=", "
			r_id = str(record.ressource.class_type)+":"+str(record.ressource.id)+","
			buff += "('"+record.urlRecord.url+"', '"+r_id+"', '"+str(record.urlRecord.lastvisited)+",')"
				
		cur = self.con.cursor()
		cur.execute("INSERT INTO "+self.table+" (url, ressources, times) VALUES "+buff+" ON DUPLICATE KEY UPDATE ressources=CONCAT(ressources, VALUES(ressources)), times=CONCAT(times, VALUES(times)" )			
		self.con.commit()

		cur.close()


class RedisUrlsManager:
	def __init__(self, conn=None):
		self.conn = conn if conn != None else RedisFactory.getConn()
		
	def get( self, key):
		buff = self.conn.get(  'ressource_'+key )
		buff = buff.split(":")
		return Ressource( int(buff[1]), int(buff[0]))
		
	def add( self, ressources, urls):
		"""
			url_hasofurl => type_class:id
		"""
		for (ressource,url) in (ressources,urls) :
			self.conn.set(  'ressource_'+urls.lasthash , ressource.getClass_type()+":"+ressource.getId())


#Static function

MAX_REFRESHRATE = 10

class UrlRecord:
	def __init__(self,url, lastvisited=-1, lastcontrolled=-1, lasthash="", refreshrate=1):
		self.data = url
		self.lastvisited = lastvisited
		self.lastcontrolled = lastcontrolled #by a master
		self.lasthash=lasthash
		self.refreshrate = refreshrate #highter => higher delay between to crawl 
		
	def incr():
		if self.refreshrate < MAX_REFRESHRATE:
			self.refreshrate+=1
	
	def decr():
		if self.refreshrate > 1 :
			self.refreshrate-=1
	
	def is_alive(self, delay):
		return time.time() - self.lastcontrolled <  self.refreshrate * delay
		
	def is_expediable(self, delay):
		return time.time() - self.lastvisited >  self.refreshrate * delay


