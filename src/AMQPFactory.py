from amqp import *

def getConn():
	return Connection(host='92.222.72.175:5672', userid='artemis',password='artemis', virtual_host='/', insist=False)
