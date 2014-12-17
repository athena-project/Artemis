#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#	@author Severus21
#


import SQLFactory
from math import *

con = SQLFactory.getConn()

def doublon( table ):
	cur = con.cursor()
	cur.execute("SELECT COUNT(id),url AS nbr_doublon, url FROM "+table+" GROUP BY url HAVING   COUNT(url) > 1")
	
	for row in cur: #url is a unique id
		print( "nbr doublon : ", row[0], " url : ",row[1])
	cur.close()

def avgSize( table ):
	size = -1
	
	cur = con.cursor()
	cur.execute('SELECT AVG( size ) FROM( SELECT SUBSTRING(sizes, 1,LOCATE( ":", sizes)-1) AS size FROM '+table+' ) AS T1')
	
	for row in cur: #url is a unique id
		size = row[0]
	cur.close()
	return floor(size)
	
def duration(table):
	duration = -1
	cur = con.cursor()
	cur.execute('SELECT MAX(lastUpdate) - MIN(lastUpdate) AS duration FROM '+table)
	
	for row in cur: #url is a unique id
		duration = row[0]
	cur.close()
	return duration
	
def count(table):
	count = -1
	cur = con.cursor()
	cur.execute('SELECT COUNT(id) AS c FROM '+table)
	
	for row in cur: #url is a unique id
		count = row[0]
	cur.close()
	return count



def speed(table):
	return count(table)/duration(table)

def countUpdate(table):
	count = -1
	cur = con.cursor()
	cur.execute('SELECT COUNT(id) AS c FROM '+table+' WHERE sizes LIKE "%:%"' )
	
	for row in cur: #url is a unique id
		count = row[0]
	cur.close()
	return count

def truncate(table):
	cur = con.cursor()
	cur.execute('TRUNCATE '+table )
	cur.close()
	
print( 'speed          ', speed("html") )
print( 'taille moyenne ', avgSize("html") )

