from time import sleep
from artemis.network.Reports import MonitorReport
from artemis.Admin import AdminClient
import json

monitors_map = json.load( open('/usr/local/conf/artemis/monitors.json', 'r') )
monitors = {}
for _host, _port in monitors_map.items():
	monitors[(_host, _port)] = MonitorReport(_host, int(_port) ) 

client = AdminClient( monitors )

while True: #si client meurt le serveur meurt
	client.refresh()
	client.print_masters_results()
	#client.print_monitors_results()
	#client.print_slaves_results()
	client.print_slaves_metrics()
	#client.print_netTree()
	sleep(5)
