# coding: utf-8
import configparser
import argparse

from artemis.Task import buildFromURIs, Task
from artemis.Utility import serialize
from artemis.network.TcpClient import TcpClient
from artemis.network.Msg import Msg, MsgType



parser 	= argparse.ArgumentParser()
parser.add_argument("--host", 	help="hostname", required=True, dest="host")
parser.add_argument("--port", 	help="port", type=int, required=True, dest="port")
args	= parser.parse_args()

host = args.host
port = args.port

config = configparser.ConfigParser()
config.optionxform=str
config.read('/usr/local/conf/artemis/gateway.ini')


def configDict2boolDict(cDict):
	d={}
	for key in cDict:
		d[key]=cDict.getboolean(key)
	return d


tasks		= []
tasks.extend( buildFromURIs(
	[ "http://"+url for url in config["HTTP"] ] ))
tasks.extend( buildFromURIs(
	[ "https://"+url for url in config["HTTPS"] ] ))
tasks.extend( buildFromURIs(
	[ "ftp://"+url for url in config["FTP"] ], True ))
tasks.extend( buildFromURIs(
	[ "ftps://"+url for url in config["FTPS"] ], True ))
#tasks.extend( buildFromURIs(
	#[ "magnet:?xt=urn:btih:012a5aceef646d37aed17c7c6298cc77fa62e63d&dn=JavaScript+Application+Design+-+A+Build+First+Approach+-+1st+Ed&tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80&tr=udp%3A%2F%2Fopen.demonii.com%3A1337&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969&tr=udp%3A%2F%2Fexodus.desync.com%3A6969"]))
		
import socket, ssl

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

context = ssl.create_default_context()
context.load_cert_chain(certfile="/usr/local/certs/artemis/client.crt", keyfile="/usr/local/certs/artemis/client.key", password="none")
context.load_verify_locations("/usr/local/certs/artemis/server.crt")
context.verify_mode = ssl.CERT_REQUIRED
context.check_hostname=False

sock = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=host)
sock.connect((host, port))


msg = serialize( Msg(MsgType.SLAVE_IN_TASKS, tasks ) )
print("connected")

if( len(msg) != sock.send(msg) ):
	print( "Error, send not complet ")

print("msg sent")
sock.shutdown(socket.SHUT_WR)
sock.close()
