#!/bin/bash
	
#	    	#
##         	##
###Iptable	###
##	   		##
#	    	#

#On supprime les règles existantes
iptables -t filter -F
iptables -t filter -X

#On bloque tout le traffic 
iptables -t filter -P INPUT DROP
iptables -t filter -P FORWARD DROP
iptables -t filter -P OUTPUT DROP

#On garde les connexions déjà ouverte
iptables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -m state --state RELATED,ESTABLISHED -j ACCEPT

#On autorise le loopback ie on autorise localhost 
iptables -t filter -A INPUT -i lo -j ACCEPT
iptables -t filter -A OUTPUT -o lo -j ACCEPT

#Gestion des ports
	#SSH
	iptables -t filter -A OUTPUT -p tcp --dport 22 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 22 -j ACCEPT
		
	#FTP
	iptables -t filter -A OUTPUT -p tcp --dport 20 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 20 -j ACCEPT
	iptables -t filter -A OUTPUT -p tcp --dport 21 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 21 -j ACCEPT
	
	#HTTP
	iptables -t filter -A OUTPUT -p tcp --dport 80 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 80 -j ACCEPT
	
	#HTTPS
	iptables -t filter -A OUTPUT -p tcp --dport 443 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 443 -j ACCEPT
	
	#Ping
	iptables -t filter -A INPUT -p icmp -j ACCEPT
	iptables -t filter -A OUTPUT -p icmp -j ACCEPT
	
	#DNS
	iptables -t filter -A OUTPUT -p tcp --dport 53 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 53 -j ACCEPT
	iptables -t filter -A OUTPUT -p udp --dport 53 -j ACCEPT
	iptables -t filter -A INPUT -p udp --dport 53 -j ACCEPT

	# NTP (horloge du serveur) 
	iptables -t filter -A OUTPUT -p udp --dport 123 -j ACCEPT

	#Rsync
	iptables -t filter -A OUTPUT -p tcp --dport 837 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 837 -j ACCEPT
	
	#MySQL
	iptables -t filter -A OUTPUT -p tcp --dport 3306 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 3306 -j ACCEPT
	
	#epmd
	iptables -t filter -A OUTPUT -p tcp --dport 4369 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 4369 -j ACCEPT

	#(if MQTT is enabled)
	iptables -t filter -A OUTPUT -p tcp --dport 1883 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 1883 -j ACCEPT
	iptables -t filter -A OUTPUT -p tcp --dport 8883 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 8883 -j ACCEPT

	#(AMQP 0-9-1 without and with TLS)
	iptables -t filter -A OUTPUT -p tcp --dport 5672 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 5672 -j ACCEPT
	iptables -t filter -A OUTPUT -p tcp --dport 5671 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 5671 -j ACCEPT

	#(if management plugin is enabled)
	iptables -t filter -A OUTPUT -p tcp --dport 15672 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 15672 -j ACCEPT

	#Erlang distribution
	iptables -t filter -A OUTPUT -p tcp --dport 25672 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 25672 -j ACCEPT

	#(if STOMP is enabled)
	iptables -t filter -A OUTPUT -p tcp --dport 61613 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 61613 -j ACCEPT
	iptables -t filter -A OUTPUT -p tcp --dport 61614 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 61614 -j ACCEPT

	#Torrent
	iptables -t filter -A OUTPUT -p tcp --dport 6881:6891 -j ACCEPT
	iptables -t filter -A INPUT -p tcp --dport 6881:6891 -j ACCEPT
	
#Protection contre le déni de service, on limite le nbr de connexion à 10co/s
iptables -A FORWARD -p tcp --syn -m limit --limit 200/second -j ACCEPT	
iptables -A FORWARD -p udp -m limit --limit 200/second -j ACCEPT
iptables -A FORWARD -p icmp --icmp-type echo-request -m limit --limit 10/second -j ACCEPT

	
