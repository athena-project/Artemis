import pickle

def serialize( obj ):
	return pickle.dumps( obj, protocol=4 )

def unserialize( data ):
	return pickle.loads( data )
