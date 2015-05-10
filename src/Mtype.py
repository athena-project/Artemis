class Mint:
	def __init__( v ):
		self.value = v
	
	def __eq__(self, value):
		return self.value == value
	
	def __le__(self, value):
		return self.value<=value
		
	def __lt__(self, value):
		return self.value<value
	
	def __mod__(self, value):
		return self.value % value

	def __mul__(self, value):
		return self.value * value
		
	def __ne__(self, value):
		return self.value != value
