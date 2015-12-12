from .HTTPDefaultHandler import HTTPDefaultHandler
from .FTPDefaultHandler import FTPDefaultHandler
from collections import defaultdict

handler_rules={
	"http": defaultdict( lambda : HTTPDefaultHandler ), 
	"https": defaultdict( lambda : HTTPDefaultHandler ), 
	"ftp": defaultdict( lambda : FTPDefaultHandler ), 
	"ftps": defaultdict( lambda : FTPDefaultHandler ), 
}

def getHandler( task ):
	handlers = handler_rules[task.scheme]
	return handlers[ task.netloc ]
		 
