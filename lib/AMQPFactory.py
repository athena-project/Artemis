from amqp import *

def getConn():
	return Connection(host='localhost:5672', userid='artemis',password='artemis', virtual_host='/', insist=False)
