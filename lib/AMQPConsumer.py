import AMQPFactory
from amqp import *



class AMQPConsumer:
	def __init__(self, key, ack=False):
		self.conn 	= AMQPFactory.getConn()
		self.key	= key
		self.channel=channel = self.conn.channel()
		
		if ack:
			self.channel.basic_qos(0 , 10, False)
		self.channel.queue_declare(self.key, durable=False)
	def __del__(self):
		self.conn.close()
	

	def consume(self):
		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		while True:
			self.channel.wait()

	def proccess(self, msg):
		if ack:
			self.channel.basic_ack(msg.delivery_tag)
