from amqp import *

def getConn():
	return Connection(host='localhost', userid='artemis',password='artemis', virtual_host='/', insist=False)
