#Artemis - a scalable, decentralized and fault-tolerant web crawler.


##Features
 - Supports http(s)/ftp(s)/tor hidden service/magnet URIs
 - Supports ftp/http basic/http digest authentifications and authentication forms
 - Supports specific handlers ( based on URIs rules)
 - Tailored crawl based on URI/content-type/time
 - Smart crawl to reduce bandwidth consumption
 
##Install

###Needed dependencies
 - Python3.4 or highter
 - Tor relay on each slave
 - transmission-daemon on each slave

###Config
 - Master config : See config_path/master.ini 
 - Monitor config : See config_path/monitor.ini 
 - Slave config : See config_path/slave.ini
 - Gateway : See config_path/gateway.ini 
 
 NB : default_config_path = /etc/artemis

 ######Warning : Do not used the SSL certificats provided( for debug only )

##Quickstart
```
 python3.4 slave.py  #To start a slave node
 python3.4 master.py  #To start a master node
 python3.4 monitor.py  #To start a monitor node
 python3.4 gateway.py --host a_master_ip --port a_netarea_of_the_selected_master  #To init crawl
```
