from artemis.Netarea import MAX
import time
import artemis.Utility as utility

#for human, https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


class AbstractReport:
	def __init__(self, host, port, lifetime=4):
		self.host 		= host
		self.port		= port
		
		self.lifetime	= lifetime
		self.deathtime	= time.time() + lifetime

	def id(self):
		return hash( (self.host, self.port) )
		
	def is_expired(self):
		return time.time() > self.deathtime
		
	def serialize(self):
		return utility.serialize(self)
		
	def unserialize(self, data):
		self = utility.unserialize( data )
		
	def update(self, n):
		self.host 		= n.host
		self.port 		= n.port
		self.deathtime 	= n.deathtime
	
	def reset(self):
		self.deathtime	= time.time() + self.lifetime
		
class Report(AbstractReport):
	# host,port : coordonnées pour le contacter
	def __init__(self, host, port, used_ram, max_ram, lifetime=4):
		AbstractReport.__init__(self, host, port, lifetime)
		self.used_ram 	= used_ram
		self.max_ram 	= max_ram

	def load(self):
		return float(self.used_ram)/self.max_ram
		
	def __ge__(self, that):
		return self.load() >= that.load()

	def __gt__(self, that):
		return self.load() > that.load()
		
	def __le__(self, that):
		return self.load() <= that.load()

	def __lt__(self, that):
		return self.load() < that.load()
		
	def is_overload(self):
		return self.load()>0.85
		
	def update(self, n):
		AbstractReport.update(self, n)
		self.used_ram 	= n.used_ram
		self.max_ram 	= n.max_ram
	
	def __str__(self):
		return ("host=%s, port=%d, used_ram=%s/%s" % (self.host, self.port, sizeof_fmt(self.used_ram), sizeof_fmt(self.max_ram)) )
		
class NetareaReport(Report):
	"""
		@param netarea uniqu id (str)
		@param weight = plus c'est grarnad plus la partition est importante : servira à l'allouer à un Netareamanger robuste load balancibg
	"""
	def __init__(self, host, port, netarea, used_ram, max_ram, next_netarea=MAX, lifetime=4):
		#netarea is an hash ie heaxdigit str
		Report.__init__(self,host, port, used_ram, max_ram, lifetime)
		self.netarea 		= netarea # [netarea,next_netarea[
		self.next_netarea 	= next_netarea
		
	def split(self):
		mid = floor( (next_netarea-netarea) / 2.0 )
		
		self.used_ram = 0
		self.next_netarea = mid
		return NetareaReport(self.host, -1, h, 0, self.max_ram, next_netarea, self.lifetime )#number_port will be update later by the master
	
class MasterReport(Report):
	def __init__(self, host, port, num_core, max_ram, maxNumNetareas, 
	netarea_reports, lifetime=4):
		self.host			= host
		self.port			= port
		self.num_core		= num_core
		self.maxNumNetareas	= maxNumNetareas
		self.netarea_reports= netarea_reports
		
		self.deathtime	= time.time() + lifetime
	
	def load(self):
		return float(len(self.netarea_reports))/self.maxNumNetareas
	
	def is_overload(self):
		return self.maxNumNetareas <= len( self.netarea_reports)
	
	def allocate(self, net):
		self.netarea_reports.append( net )

	def __str__(self):
		return ("host=%s, port=%d, netareas=%d/%d\n\t%s" %
			(self.host, self.port, len(self.netarea_reports),  
			self.num_core, '\n\t'.join([str(n) for n in self.netarea_reports])))
			
class SlaveReport(Report):
	def __init__(self, host, port, used_ram, max_ram, lifetime=4):
		Report.__init__(self, host, port, used_ram, max_ram, lifetime)
	
class SlaveMetrics(AbstractReport):
	def __init__(self, host, port, tasks_processed, delay, lifetime=4):
		AbstractReport.__init__(self, host, port, lifetime)
		self.tasks_processed = tasks_processed
		self.delay 			 = delay
	
	def speed(self):
		return float(self.tasks_processed) / float(self.delay)	
		
	def __str__(self):
		return ("""host=%s, port=%d, %d  tasks processed in %d s at 
			%ft/s""" % (self.host, self.port, self.tasks_processed, 
			self.delay, self.speed()) )

class MonitorReport(Report):
	def __init__(self, host, port, lifetime=60):
		Report.__init__(self, host, port, 0, 0, lifetime)
