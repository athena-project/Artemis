from time import sleep
from artemis.network.Reports import MonitorReport
from artemis.Admin import AdminClient

m = MonitorReport("127.0.1.1", 1984)
client = AdminClient(
	{m.id(): m}
)

while True: #si client meurt le serveur meurt
	client.refresh()
	client.print_masters_results()
	#client.print_monitors_results()
	#client.print_slaves_results()
	client.print_slaves_metrics()
	#client.print_netTree()
	sleep(5)
