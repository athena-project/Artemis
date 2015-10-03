import redis

def getConn():
	return redis.StrictRedis(host='92.222.72.175', port=6379, db=0)
