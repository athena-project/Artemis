import redis

def getConn():
	return redis.StrictRedis(host='92.222.70.24', port=6379, db=0)
