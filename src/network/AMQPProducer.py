from .AMQPFactory import *
from amqp import *
import logging

class AMQPProducer:
	def __init__(self, key):
		self.conn 	= getConn()
		self.key	= key
		self.channel= self.conn.channel()
		
		self.channel.queue_declare(self.key, durable=False)
		
	def terminate(self):
		self.conn.close()
	
	def add_task(self, task, exchange="", routing_key="" ):		
		msg 	= Message( task )
		msg.properties["delivery_mode"] = 2 #make it persitant
		
		self.channel.basic_publish(msg, exchange=exchange, routing_key=(routing_key if routing_key else self.key))
	
	def add_task_fanout(self, task, exchange=""):
		msg 	= Message( task )
		msg.properties["delivery_mode"] = 2 #make it persitant
		
		self.channel.basic_publish(msg, exchange=exchange)
