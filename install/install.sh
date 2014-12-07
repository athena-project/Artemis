#!/bin/sh

CURRENT_DIR=`dirname $0` #Dossier parent du script d'installation
ARTEMIS_BIN="/usr/opt/artemis"
ARTEMIS_CONF="/etc/artemis"


###
### BEGIN DEPENDENCES
###

# General
apt-get update
apt-get upgrade
#apt-get install build-essential cmake
apt-get install -y python3-dev python3-pip

##Redis
#wget http://download.redis.io/redis-stable.tar.gz
#tar xvzf redis-stable.tar.gz
#cd redis-stable
#make
#make install

#cd ..
#rm -r redis-stable
#rm redis-stable.tar.gz

#config ?
pip3 install  redis

##MySQL
#apt-get install mysql-server
#mysql -u root -p"rj7@kAv;8d7_e(E6:m4-w&" -e "CREATE DATABASE artemis"
#mysql -u root -p"rj7@kAv;8d7_e(E6:m4-w&" -D artemis -e "SOURCE tables.sql"
#config ?
pip3 install  PyMySQL

###
### END DEPENDENCES
###


###
### BEGIN STRUCTURE
###
mkdir /usr/opt
mkdir /usr/opt/artemis
mkdir /etc/artemis 

ln -s /usr/opt/mnemosyne/libpyRessource.so   /usr/opt/artemis/libpyRessource.so  #petit pb de lib


cp $CURRENT_DIR/../conf/* $ARTEMIS_CONF
cp $CURRENT_DIR/../lib/*  $ARTEMIS_BIN

cp $CURRENT_DIR/init/* /etc/init.d/
chmod 0755 /etc/init.d/artemis-master
chmod 0755 /etc/init.d/artemis-slave


mkdir /var/log
mkdir /var/log/artemis
###
### END STRUCTURE
###



###
###	BEGIN FIREWALL
###
cp $CURRENT_DIR/firewall.sh /etc/init.d/firewall.sh
		
chmod +x /etc/init.d/firewall.sh
/etc/init.d/firewall.sh
		
update-rc.d firewall.sh defaults
###
###	END FIREWALL
###
