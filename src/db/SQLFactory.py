import pymysql

def getConn():
	return pymysql.connect(database='artemis', host='localhost', user='root',
							passwd='rj7@kAv;8d7_e(E6:m4-w&', connect_timeout=200)
