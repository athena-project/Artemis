#!/bin/sh

CURRENT_DIR=`dirname $0` #Dossier parent du script d'installation
ARTEMIS_BIN="/usr/opt/artemis"
ARTEMIS_CONF="/etc/artemis"
ARTEMIS_LOG="/var/log/artemis"


###
### BEGIN DEPENDENCES
###

# General
apt-get update
apt-get upgrade
apt-get install -y python3-dev python3-pip 


##MySQL
apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 1BB943DB
echo deb http://ftp.igh.cnrs.fr/pub/mariadb//repo/5.5/ubuntu $(lsb_release -sc) main | sudo tee /etc/apt/sources.list.d/MariaDB.list 
apt-get update
apt-get install -y mariadb-server mariadb-client

#apt-get install mysql-server
mysql -u root -p"rj7@kAv;8d7_e(E6:m4-w&" -e "CREATE DATABASE artemis"
mysql -u root -p"rj7@kAv;8d7_e(E6:m4-w&" -D artemis -e "SOURCE tables.sql"
#config ?
pip3 install  PyMySQL


##RabbitMQ
pip3 install amqp

##Tor
wget https://www.torproject.org/dist/torbrowser/4.5.3/tor-browser-linux64-4.5.3_en-US.tar.xz
tar -Jxvf tor-browser-linux64-4.5.3_en-US.tar.xz
apt-get install python-stem
pip3 install pysocks 

##Formasaurus
apt-get install libamd2.3.1 libblas3gf libc6 libgcc1  libgfortran3 liblapack3gf libumfpack5.6.2 libstdc++6 build-essential gfortran python3-all-dev libatlas-base-dev
pip3 install numpy sklearn scipy formasaurus 

#torrent
apt-get install -y transmission-deamon python3-libtorrent #config rpc-auth = false, ratio_limit=0 no seeding see set.json, max torrent paralle à definir ici aussi
pip3 install transmissionrpc 

###
### END DEPENDENCES
###


###
### BEGIN STRUCTURE
###
mkdir -p $ARTEMIS_BIN
mkdir -p $ARTEMIS_CONF
mkdir -p $ARTEMIS_LOG

ln -s /usr/opt/mnemosyne/libpyRessource.so   $ARTEMIS_BIN/extras/libpyRessource.so  #petit pb de lib

cp $CURRENT_DIR/../conf/* $ARTEMIS_CONF
cp $CURRENT_DIR/../artemis/*  $ARTEMIS_BIN
cp -r $CURRENT_DIR/../extras  $ARTEMIS_BIN
cp $CURRENT_DIR/../log/* $ARTEMIS_LOG

chmod 0711 $ARTEMIS_CONF
chmod 0711 $ARTEMIS_BIN
chmod 0711 $ARTEMIS_LOG

mv tor-browser_en-US/Browser/TorBrowser/Tor $ARTEMIS_BIN/extras/Tor
rm -r tor-browser_en-US
rm tor-browser-linux64-4.5.3_en-US.tar.xz


###
### END STRUCTURE
###



###
###	BEGIN FIREWALL
###
cp $CURRENT_DIR/firewall.sh /etc/init.d/artemis-firewall.sh
		
chmod +x /etc/init.d/artemis-firewall.sh
cd /etc/init.d/artemis-firewall.sh
		
update-rc.d artemis-firewall.sh defaults
##
##	END FIREWALL
##
