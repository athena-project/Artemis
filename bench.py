from artemis.network.TcpServer import T_TcpServer
from artemis.network.TcpClient import TcpClient
from artemis.network.Msg import Msg
from time import sleep, time
from threading import Event
import sys
def test():
	e=Event()
	s = T_TcpServer(e)
	s.start()
	sleep(0.001)
	c = TcpClient()
	
	
	d = "a"*10000
	print( sys.getsizeof(d) )
	t = time()
	for k in range(4096):
		c.send( Msg(0,d), '127.0.0.1', s.port)
	while( len(c.waiting)> 0):
		sleep(0.1)
	print("end ", time()-t)
test()	

