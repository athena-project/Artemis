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
#	@autor Severus21
#


import SQLFactory

con = SQLFactory.getConn()

def doublon( table ):
	cur = self.con.cursor()
	cur.execute("SELECT COUNT(id),url AS nbr_doublon, url FROM "+table+" GROUP BY url HAVING   COUNT(url) > 1")
	
	for row in cur: #url is a unique id
		print( "nbr doublon : ", row[0], " url : ",row[1])
	cur.close()

def avgSize( table ):
	cur = self.con.cursor()
	cur.execute("SELECT AVG(sizes) FROM "+table)
	
	for row in cur: #url is a unique id
		print( "taille moyenne : ", row[0])
	cur.close()
	
