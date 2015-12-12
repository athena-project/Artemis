from time import time

class Timer:  
    def __enter__(self):  
        self.start()  
        return self  
      
    def __exit__(self, *args, **kwargs):   
        self.stop()  
      
    def start(self):  
        if hasattr(self, 'interval'):  
            del self.interval  
        self.start_time = time()  
  
    def stop(self):  
        if hasattr(self, 'start_time'):  
            self.interval = time() - self.start_time  
            del self.start_time    
