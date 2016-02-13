#!/bin/bash

f_admin=
f_master=
f_monitor=
f_slave=

f_with_deps= #install dependancies

usage="\
Usage: $0 [OPTION]

Options:
	--all			Install the four modules
	--admin			Install the admin module
	--master		Install the master module
	--monitor		Install the monitor module
	--slave			Install the slave module
	
	--with_deps 	Try to install all needed dependancies
"

while test $# -ne 0; do
	case $1 in    
    --all) 
		f_admin=true
		f_master=true
		f_monitor=true
		f_slave=true
    ;;
	
	--admin)
		f_admin=true
	;;
	
	--master)
		f_master=true
	;;
	
	--monitor)
		f_monitor=true
	;;
	
	--slave)
		f_slave=true
	;;

	--with_deps)
		f_with_deps=true
	;;
	
    --help) echo "$usage"; exit $?;;

    --version) echo "$0 $scriptversion"; exit $?;;

    --)	shift
	break;;

    -*)	echo "$0: invalid option: $1" >&2
	exit 1;;

    *)  break;;
	esac  
	
	shift
done

if test -n "$f_with_deps"; then
	apt-get install -y python3-pip 
	pip3 install termcolor
	
	#if test -n "$f_admin"; then fi
	
	if test -n "$f_master"; then 
		apt-get install -y libtorrent-dev python3-libtorrent
	fi
	
	if test -n "$f_monitor"; then 
		pip3 install blist
	fi
	
	if test -n "$f_slave"; then 
		apt-get install -y libtorrent-dev python3-libtorrent
		
		#lxml
		apt-get install -y python3-lxml
		
		#tor
		apt-get install -y tor python3-stem
		pip3 install pysocks 
		
		#formasaurus
		apt-get install -y libamd2.3.1 libblas3gf libc6 libgcc1  
		apt-get install -y libgfortran3 liblapack3gf libumfpack5.6.2 
		apt-get install -y libstdc++6 build-essential gfortran  
		apt-get install -y libatlas-base-dev python3-all-dev
		pip3 install numpy sklearn sklearn-crfsuite scipy formasaurus
		
		#torrent
		apt-get install -y transmission-daemon python3-libtorrent
		pip3 install transmissionrpc 
		
		transmission-daemon stop
		mv install/conf/transmission/settings.json /etc/transmission-daemon/settings.json
		transmission-daemon start
	fi
fi

mkdir -p "/var/log/artemis"
mkdir -p "/usr/local/bin/artemis"
mkdir -p "/tmp/artemis"

cp *.py "/usr/local/bin/artemis"
python3.4 setup.py install

