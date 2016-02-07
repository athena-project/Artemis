from .AMQPFactory import *
from amqp import *



class AMQPConsumer:
	def __init__(self, key=None, ack=False):
		self.conn 		= getConn()
		self.channel 	= self.conn.channel()
		self.ack		= ack
		
		if ack:
			self.channel.basic_qos(0 , 10, False)
				
		if key != None:
			self.key	= key
			self.channel.queue_declare(self.key, durable=False)
		else:
			result = self.channel.queue_declare(exclusive=True)
			self.key = result.queue
			
	def terminate(self):
		self.conn.close()

	def consume(self):
		self.channel.basic_consume(callback=self.proccess, queue=self.key)
		while True:
			self.channel.wait()

	def process(self, msg):
		if self.ack:
			self.channel.basic_ack(msg.delivery_tag)
