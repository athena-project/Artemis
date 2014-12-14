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
# coding: utf-8

import configparser
import Slave

import logging
logging.basicConfig(filename="/var/log/artemis/error.log", format='%(asctime)s  %(levelname)s  %(message)s',
	level=logging.INFO)

def configDict2boolDict(cDict):
	d={}
	for key in cDict:
		d[key]=cDict.getboolean(key)
	return d


config = configparser.ConfigParser()
config.read('/etc/artemis/slave.ini')

s=Slave.Slave(
	useragent		= config['General']['useragent'],  
	period			= int( config['General']['period'] ), 
	maxWorkers		= int( config['Thread']['maxWorkers'] ),
	contentTypes	= configDict2boolDict( config['ContentTypes'] ), 
	delay			= int( config['Update']['delay'] ),
	maxCrawlers		= int( config['Thread']['maxCrawlers'] ),
	sqlNumber		= int( config['SQL']['number'] )
)

s.harness()
