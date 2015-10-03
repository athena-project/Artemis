from ftplib import FTP, FTP_TLS
from urllib.parse import urljoin
from artemis.Task import Task, NO_AUTH, AUTH_FTP, TASK_WEB_STATIC
import datetime 
import tempfile
import io

def previous(elmts, pos, n):
	if n == 0 :
		raise Exception( "Previous not found")
	
	if not elmts[ pos ]:
		return previous(elmts, pos-1, n-1)
	else :
		return pos
		
def parseLine(line):
	elmts	= line.split(" ")
	permission 	= elmts[0]
	
	pos 		= previous( elmts, -1, len(elmts) )
	name		= elmts[pos]
	pos 		= previous( elmts, pos-1, len(elmts) )
	date		= elmts[pos]
	pos 		= previous( elmts, pos-1, len(elmts) )
	date		= elmts[pos]+" "+date
	pos 		= previous( elmts, pos-1, len(elmts) )
	date		= elmts[pos]+" "+date
	pos 		= previous( elmts, pos-1, len(elmts) )
	size		= elmts[pos]
	
	
	try: #'%b %d %H:%M' : Jun 06 10:19 assuming current year
		dt	= datetime.datetime.strptime( date, '%b %d %H:%M')
		dt	= dt.replace( datetime.date.today().year ) 
		lastModified= dt.timestamp()
	except Exception:
		try: #'%b %d  %Y' : "Jan 16  2012"
			dt	= datetime.datetime.strptime( date, '%b %d %H:%M')
			lastModified= dt.timestamp()
		except Exception:	
			lastModified= -1

	return ( permission, size, lastModified, name, permission[0]=="d") #[4] => idDir?


class FTPDefaultHandler:
	def __init__(self,  accreditationCacheHandler, proxy=None):
		self.accreditationCacheHandler 	= accreditationCacheHandler
		self.proxy						= proxy
		
	def getAccreditation(self, task, ftp):
		if self.proxy:
			if task.auth == NO_AUTH :
				ftp.login("anonymous@"+task.netloc, "anonymous")
			elif task.auth == AUTH_FTP :
				login, pwd	= self.accreditationCacheHandler.get(task.auth, task )
				ftp.login(login+"@"+task.netloc, pwd)
		else:
			if task.auth == NO_AUTH :
				ftp.login()
			elif task.auth == AUTH_FTP :
				login, pwd	= self.accreditationCacheHandler.get(task.auth, task )
				ftp.login(login, pwd)
	
	def execute_dir(self, task, ftp, ):
		newTasks	= []
		lines	= []

		ftp.cwd( task.path[1:] if task.path and task.path[0]=="/" else task.path ) 
		ftp.dir( lines.append )
		
		for line in lines:
			( permission, size, lastModified, name, is_dir)	= parseLine( line )
			#print("current uri: ",task.url) 
			#print("current name: ",name) 
			newTasks.append( Task( url=urljoin(task.url+"/", name), nature=TASK_WEB_STATIC, auth=task.auth, is_dir=is_dir))
			#print("line ", line)
			#print("ntask ", urljoin(task.url+"/", name))
		return (newTasks, None)
			
	def execute(self, task):
		buff 		= []
		
		if self.proxy: #not test yet
			ftp =  FTP() if True else FTP_TLS()
			ftp.connect( self.proxy[0], self.proxy[1])
		else:
			ftp =  FTP(task.netloc) if True else FTP_TLS(task.netloc)
		
		self.getAccreditation( task, ftp)
		
		if task.is_dir :
			return self.execute_dir(task, ftp)
		else:
			metaBuff	= io.BytesIO()
			ftp.retrbinary("LIST " + task.path , metaBuff.write)
			( permission, size, lastModified, name, is_dir)	= parseLine( str(metaBuff.getvalue().decode("utf-8"))  )

			if task.lastvisited > lastModified : 
				task.incr()
			elif is_dir:
				task.is_dir = True
				return self.execute_dir(task, ftp)
			else:	
				tmpFile	= tempfile.SpooledTemporaryFile(max_size=1048576) #1Mo
				ftp.retrbinary("RETR " + task.path, tmpFile.write)


			return [], tmpFile
