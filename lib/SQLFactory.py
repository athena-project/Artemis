import pymysql

def getConn():
	return pymysql.connect(database='artemis', host='92.222.69.29', user='root',passwd='rj7@kAv;8d7_e(E6:m4-w&', connect_timeout=2000)
