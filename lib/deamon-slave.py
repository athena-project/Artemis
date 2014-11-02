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
# coding: utf-8

import configparser
import CrawlerSlave

def configDict2boolDict(cDict):
	d={}
	for key in cDict:
		d[key]=cDict.getboolean(key)
	return d


config = configparser.ConfigParser()
config.read('conf/slave.ini')

s=CrawlerSlave.Slave(
	masterAddress	= config['General']['masterAddress'],
	useragent		= config['General']['useragent'], 
	cPort			= int( config['General']['cPort'] ), 
	port			= int( config['General']['sPort'] ), 
	period			= int( config['General']['period'] ), 
	maxWorkers		= int( config['Thread']['maxWorkers'] ),
	contentTypes	= configDict2boolDict( config['ContentTypes'] ), 
	delay			= int( config['Update']['delay'] ),
	maxSavers		= int( config['Overseer']['maxSavers'] )
)

s.harness()
