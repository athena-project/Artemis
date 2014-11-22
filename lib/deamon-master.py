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
import Url
import Master 

def configDict2boolDict(cDict):
	d={}
	for key in cDict:
		d[key]=cDict.getboolean(key)
	return d


config = configparser.ConfigParser()
config.read('../conf/master.ini')

master = Master.Master(
	useragent		= config['General']['useragent'], 
	cPort			= int( config['General']['cPort'] ), 
	port			= int( config['General']['sPort'] ), 
	period			= int( config['General']['period'] ), 
	domainRules		= configDict2boolDict( config['DomainRules'] ),
	protocolRules	= configDict2boolDict( config['ProtocolRules'] ),
	originRules		= configDict2boolDict( config['OriginRules'] ),
	delay 			= int( config['Update']['delay'] ),
	maxRamSize		= int( config['UrlHandling']['maxRamSize'] ),
	numOverseer	= int( config['General']['numOverseer'] )
)
for url in config['Gateway']:
	master.urlCacheHandler.add( Url.Url(url="http://"+url) )
master.crawl()
