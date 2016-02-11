#!/bin/bash

#General
apt-get install libtorrent-dev python3-libtorrent python3-pip 
pip3 install termcolor blist

#For slave only
#if [[ test $# == 0 ]]; then
if [ $# -eq 1 ] && [ $1 -eq 1 ]
then
	#Lxml
	apt-get install python3-lxml
	
	##Tor
	apt-get install tor python3-stem
	pip3 install pysocks 

	##Formasaurus
	apt-get install libamd2.3.1 libblas3gf libc6 libgcc1  
	apt-get install libgfortran3 liblapack3gf libumfpack5.6.2 
	apt-get install libstdc++6 build-essential gfortran python3-all-dev 
	apt-get install libatlas-base-dev
	pip3 install numpy sklearn sklearn-crfsuite scipy formasaurus  

	#torrent
	#config rpc-auth = false, ratio_limit=0 no seeding see set.json, max torrent paralle à definir ici aussi	
	apt-get install -y transmission-daemon python3-libtorrent
	pip3 install transmissionrpc 
else
	echo "aqsdfqdf"
fi
