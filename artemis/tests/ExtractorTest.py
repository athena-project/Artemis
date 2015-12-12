import unittest
from .Benchmark import Timer 
from artemis.Task import Task, TaskNature
from artemis.extractors.ExtractorFactory import init_extractor
from hermes.RessourceFactory import build as build_ressource
import pickle
import os


class ExtractorTest(unittest.TestCase):
	def test_html_extractor(self):
		filenames = [
			os.path.join( "artemis", "data", "tests", "extractor_f_1.html"),	]
		tasks = [
			Task("""https://fr.wikipedia.org/wiki/Wikip%C3%
			A9dia:Accueil_principal""")]
		all_links = []
		
		for filename in filenames :
			with open( filename+"_1", "rb") as tmp:
				all_links.append( set(pickle.load(tmp)) )
		
		for filename, task, links in zip(filenames, tasks, all_links):
			with open(filename, "rb") as html_file :
				ressource = build_ressource( html_file, "text/html")
				extractor = init_extractor( ressource, task)
				tmp = extractor.extract( html_file )
				
				tmp_links = [ t.url for t in tmp ]
				self.assertTrue(  links.difference( set(tmp_links)) != links )
		
	def test_sitemap_extractor(self):
		filenames 	= [
			os.path.join( "artemis", "data", "tests", "extractor_f_2.xml"),
		]
		tasks		= [ Task("https://www.ovh.com/sitemap.xml", 
			nature=TaskNature.web_static_sitemap)]
		all_links	= []
		
		for filename in filenames :
			with open( filename+"_1", "rb") as tmp:
				all_links.append( set(pickle.load(tmp)) )
		
		for filename, task, links in zip(filenames, tasks, all_links):
			with open(filename, "rb") as sitemap_file:
				ressource = build_ressource( sitemap_file, "text/xml")
				extractor = init_extractor( ressource, task)
				tmp = extractor.extract( sitemap_file )
				
				tmp_links = [ t.url for t in tmp ]
				self.assertTrue( not links.difference( set(tmp_links)) )

	def test_directory_extractor(self):
		dirnames	= [ os.path.join( "artemis", "data", "tests", "extractor_d_1") ]
		filenames = [
			os.path.join( "artemis", "data", "tests", "extractor_f_1.html")]
		tasks		= [ Task("https://fr.wikipedia.org/", 
			nature=TaskNature.web_static, is_dir=True)
		]
		all_links	= []
		
		for filename in filenames :
			with open( filename+"_1", "rb") as tmp:
				all_links.append( set( pickle.load(tmp) ) )
		
		for dirname, task, links in zip(dirnames, tasks, all_links):
			ressource = build_ressource( dirname, "inode/directory")
			extractor = init_extractor( ressource, task)
			tmp = extractor.extract(  )
			
			tmp_links = [ t.url for t in tmp ]
			self.assertTrue( links.difference( set(tmp_links)) != links )
