import AMQPFactory
from amqp import *


class AMQPProducer:
	def __init__(self, key):
		self.conn 	= AMQPFactory.getConn()
		self.key	= key
		self.channel=channel = self.conn.channel()
		
		self.channel.queue_declare(self.key, durable=True)
		
	def __del__(self):
		self.conn.close()
	
	def add_task(self, task ):		
		msg 	= Message( task )
		msg.properties["delivery_mode"] = 2 #make it persitant
		
		self.channel.basic_publish(msg, exchange="", routing_key=self.key)
		
		
		
