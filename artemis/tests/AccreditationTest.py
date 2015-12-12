import unittest
from .Benchmark import Timer 
from artemis.accreditation.AccreditationCache import AccreditationCache
from artemis.accreditation.User import User, SqliteUserManager
from artemis.handlers.HTTPDefaultHandler import HTTPDefaultHandler
from artemis.Task import Task, TaskNature

import os
from artemis.Task import AuthNature
class AccreditationTest(unittest.TestCase):
	def test_sqlite(self):
		manager = SqliteUserManager("test_users.sql")
			#os.path.join( "data", "accreditation", "test_users.sql"))

		manager.create()
		
		users = [
			User( -1, "github_test_acc", "mdp_github_test",
				AuthNature.form, "github.com", 1 , 
				"https://github.com/login"),
			User( -1, "oc_test_acc@yopmail.com", "oc_test_acc", 
				AuthNature.form, "openclassrooms.com", 2,
				"https://openclassrooms.com/login"),	
			User( -1, "", "", AuthNature.http_basic, "wikipedia.fr"),	
			User( -1, "", "", AuthNature.http_digest, ""),	
			User( -1, "", "", AuthNature.ftp, ""),	
		]
		
		manager.insert( users )
		
		user = manager.getByNetloc( AuthNature.form, "github.com")
		self.assertEqual( user._id, 1)
		self.assertEqual( user.login, "github_test_acc")
		self.assertEqual( user.password, "mdp_github_test")
		self.assertEqual( user.auth_nature, AuthNature.form)
		
		user = manager.getByNetloc( AuthNature.form, "openclassrooms.com" )
		self.assertEqual( user._id, 2)
		self.assertEqual( user.login, "oc_test_acc@yopmail.com")
		self.assertEqual( user.password, "oc_test_acc")
		self.assertEqual( user.auth_nature, AuthNature.form)
		
	def test_cache(self):
		cache = AccreditationCache( 1024, "test_users.sql")

		items = [
			(AuthNature.form, Task( "https://openclassrooms.com/\
			membres/oc-test-accoc-test-acc", 
			nature = TaskNature.web_static, 
			auth = AuthNature.form)), 
			#(AuthNature.form, Task( "https://github.com/\
			#github_test_acc", 
			#nature = TaskNature.web_static, 
			#auth = AuthNature.form))
			]
		
		for item in items :
			cache.get( item[0], item[1] ) 
		
		for item in items :
			cache.get( item[0], item[1] ) 
		
	def test_auth(self):
		cache = AccreditationCache( 1024, "test_users.sql")
		handler = HTTPDefaultHandler("*", "*/*", cache, None)
		
		contentType, tmpfile, newTasks = handler.execute( 
			Task( "https://openclassrooms.com/membres/oc-test-accoc-test-acc", 
			nature = TaskNature.web_static, 
			auth = AuthNature.form) )
		
		tmpfile.seek(0)
		buff = str( tmpfile.read())
		
		self.assertTrue( buff.find("oc_test_acc")>-1 )
