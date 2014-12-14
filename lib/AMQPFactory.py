from amqp import *

def getConn():
	return Connection(host='localhost:5672', userid='guest',password='guest', virtual_host='/', insist=False)
