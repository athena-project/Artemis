from ftplib import FTP, FTP_TLS
from urllib.parse import urljoin
from artemis.Task import Task, AuthNature, TaskNature
from datetime import datetime
import tempfile
import io

		
def parseLine(line):
	elmts = [ l for l in line.strip().split(" ") if l ]
	permission 	= elmts[0]
	name = elmts[-3] if permission[0] == "l" else elmts[-1]
	date_pos = -3 if permission[0] == "l" else -1
	is_dir= permission[0]=="d"
	
	if is_dir :
		return ( name, -1, is_dir)
		
	#pas de convention sur la date
	try: #'%b %d %H:%M' : Jun 06 10:19 assuming current year
		delmts = elmts[date_pos-3:date_pos]
		date = "%s %s %s" % (delmts[0], delmts[1], delmts[2])		
		
		dt	= datetime.strptime( date, '%b %d %H:%M')
		dt	= dt.replace( datetime.date.today().year ) 
		lastModified= dt.timestamp()
	except Exception:
		try: #'%b %d  %Y' : "Jan 16  2012"
			date = "%s %s  %s" % (delmts[0], delmts[1], delmts[2])
			dt	= datetime.strptime( date, '%b %d  %Y')
			lastModified= dt.timestamp()
		except Exception:	
			lastModified= -1

	return ( name, lastModified, is_dir) 

class FTPDefaultHandler:
	def __init__(self,  accreditationCache, proxy=None):
		self.accreditationCache 		= accreditationCache
		self.proxy						= proxy
		
	def getAccreditation(self, task, ftp):
		if self.proxy:
			if task.auth == AuthNature.no :
				ftp.login("anonymous@"+task.netloc, "anonymous")
			elif task.auth == AuthNature.ftp :
				login, pwd	= self.accreditationCache.get(task.auth, task )
				ftp.login(login+"@"+task.netloc, pwd)
		else:
			if task.auth == AuthNature.no :
				ftp.login()
			elif task.auth == AuthNature.ftp :
				login, pwd	= self.accreditationCache.get(task.auth, task )
				ftp.login(login, pwd)
	
	def execute_dir(self, task, ftp):
		newTasks	= []
		lines	= []
		ftp.dir( lines.append )
		
		for line in lines:
			name, nothing, is_dir	= parseLine( line )
			newTasks.append( Task( url=urljoin(task.url+"/", name), 
				nature=TaskNature.web_static, auth=task.auth, is_dir=is_dir))
				
		return (newTasks, None)
			
	def execute(self, task):
		buff 		= []
		if self.proxy: #not test yet
			ftp =  FTP() if True else FTP_TLS()
			ftp.connect( self.proxy[0], self.proxy[1])
		else:
			ftp =  FTP(task.netloc) if True else FTP_TLS(task.netloc)
		
		with ftp :
			self.getAccreditation( task, ftp)
			path = task.path

			path = ( task.path[1:] if path and task.path[0]=="/" else task.path)
			if task.is_dir :
				if path:
					ftp.cwd( path ) 

				return self.execute_dir(task, ftp)
			else:
				meta	= []
				tmp 	= path.rsplit("/", 1)

				if len(tmp) == 2:
					ftp.cwd(tmp[0])
					filename = tmp[1]
				else:
					filename	= tmp[0]
				ftp.retrbinary("LIST " + filename , meta.append)
				
				if meta :
					is_dir = (len(meta) != 1)
					
					if not is_dir:
						( name, lastModified, is_dir)	= parseLine( meta[0].decode()  )
						is_dir = (name != filename)

					if is_dir:
						task.is_dir = True
						if filename:
							ftp.cwd( filename ) 

						return self.execute_dir(task, ftp)
					
					if task.lastvisited > lastModified : 
						task.incr()
						return [], None
				
				tmpFile	= tempfile.SpooledTemporaryFile(max_size=1048576) #1Mo
				ftp.retrbinary("RETR " + filename, tmpFile.write)

				return [], tmpFile
