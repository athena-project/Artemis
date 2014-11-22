Artemis
=======
Collectes raw data from multiple sources : mainly the Web. Fully write in python.

Needed dependencies
===================
  -Python3.3 or highter
  
  -A redis server
  
  -A  SQL sever
  
  -Mnemosyne

Install
=======
  $ sudo ./install.sh
  
Configure
=========
  Master configuration :
    See /etc/artemis/master.ini
    
  Slave configuration :
    See /ets/artemis/slave.ini
  
  SQL Conf :
    see SQLFactory.py
  
  Redis Conf :
    see RedisFactory.py

Qickstart
=========
  sudo /etc/init.d/artemis-{master|slave} start
  
  or 
  
  python3.* deamon-{master|slave}.py for debug purposes
