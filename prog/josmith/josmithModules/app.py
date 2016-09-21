import os
import sys

import util
import baseApp
import urlMatcher
import db
import baseClauses
import basePages

class App (baseApp.BaseApp, baseClauses.BaseClauses):
	def setDefault (self, attribute, value):
		if not hasattr (self, attribute):
			setattr (self, attribute, value)

	def __init__ (self, siteFileName, siteModuleName):
		self.siteFileName = siteFileName
		self.siteModuleName = siteModuleName
		
		util.app = self

		self.log = util.Log (self, 'error')
		self.urlMatcher = urlMatcher.UrlMatcher (self)

		self.logToFile = True
		self.debug = False
		self.forceClairvoyant = False
		self.clairChunks = []
		
		self.siteFileName = self.siteFileName.replace ('\\', '/')
		self.siteName = self.siteFileName.split ('/')[-1][:-3]
		self.siteDirName = os.path.dirname (os.path.realpath (self.siteFileName)) .replace ('\\', '/')
		sys.path.append (self.siteDirName)			

		self.localName = 'localhost:4000'
		
		self.authorizeUrl = 'authorize'
		self.LoginPage = basePages.LoginPage
		self.LoginResponsePage = basePages.LoginResponsePage
		self.LogoutResponsePage = basePages.LogoutResponsePage

		self.authorize = True
				
		self.superUserRoleName = 'super_user'		
		self.defaultUserEmailAddress = 'root@josmith.org'
		self.defaultUserPassword = 'changethis'

		self.config ()

		self.setDefault ('defaultRoleName', self.superUserRoleName)
		self.setDefault ('clairUserRoleName', self.superUserRoleName)
	
		if self.authorize:
			self.setDefault ('loginUrl', self.authorizeUrl + '/login')
			self.setDefault ('loginResponseUrl', self.authorizeUrl + '/login_response')
			self.setDefault ('logoutResponseUrl', self.authorizeUrl + '/logout_response')
			
			self.setDefault ('authorizeUrlPatterns', [
				[self.loginUrl + '/*', self.LoginPage],
				[self.loginResponseUrl + '/*', self.LoginResponsePage],
				[self.logoutResponseUrl + '/*', self.LogoutResponsePage],
			])
			
			self.urlPatterns += self.authorizeUrlPatterns
			
		self.urlMatcher.getUrlPatterns ()
		
		self.setDefault ('dbDirName', self.siteDirName + '/db')
		self.setDefault ('dbFileName', self.dbDirName + '/' + self.siteName + '.db')
				
		if self.siteModuleName == '__main__':
			self.domainName = self.localName

		self.setDefault ('staticDirName', self.siteDirName + '/static')
		self.setDefault ('logDirName', self.staticDirName + '/log')
		self.setDefault ('logFileNameTemplate', self.logDirName + '/' + self.siteName + '_{0}.log')		
		self.log ('application restarted', context = 'initialization', lead = '\n\n\n')
			
		self.setDefault ('cookieName', self.domainName)
		
		self.db = db.Db (self)
		self.cs = self.db.connect ()
				
		# If we started this up locally by typing 'python site.py' (with python version >= 3.5)
		if self.siteModuleName == '__main__':
			# Instantiate and start a simple test server, as defined and explained in baseApp.py
			# It will call method BaseApp.__call__ for each page request
			self.serve ()
		# If we didn't start it up that way, calling BaseApp.__call__ is left to the production server, e.g. mod_wsgi
		# This means that site.py is then a module imported by that production server, rather than the main program
