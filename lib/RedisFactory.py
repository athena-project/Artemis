import redis

def getConn():
	return redis.StrictRedis(host='localhost', port=6379, db=0)
