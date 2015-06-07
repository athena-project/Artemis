import pickle


def serialize( obj ):
	return pickle.dumps( obj )

def unserialize( data ):
	return pickle.loads( data )
