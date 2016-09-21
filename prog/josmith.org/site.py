import os
import sys

sys.path.append (os.path.dirname (os.path.realpath (__file__)) + '/../josmith')

from josmith import *

class DynamicTestPage (Page):
	def config (self):
		self.allowedRoleNames = ['super_user']

	def get (self):
		super () .get ()
		self.content = ['Dynamic test page: {}<br><a href="/{}/">Log out</a>'.format (self.args, self.app.logoutResponseUrl)]

class RestrictedStaticPage (StaticPage):
	def config (self):
		self.allowedRoleNames = ['super_user']
		
class FrameLoginResponsePage (LoginResponsePage):
	def get (self):
		super () .get ()
		self.content = [self.app.getHtmlClause ('', self.app.getScriptClause ('', '''
			parent.structure.location = '/structure';
			parent.content.location = '/{}';
		'''.format ('/'.join (self.args))))]

class FrameLogoutResponsePage (LogoutResponsePage):
	def get (self):
		super () .get ()
		self.content = [self.app.getHtmlClause ('', self.app.getScriptClause ('', '''
			parent.structure.location = '/structure';
			parent.content.location = '/{}';
		'''.format ('/'.join (self.args))))]
		
class Site (App):
	def config (self):
		self.logToFile = True
		self.debug = True
		self.authorize = True
		self.domainName = 'josmith.org'
		self.jQueryClause = self.getScriptClause ('http://code.jquery.com/jquery-latest.min.js')
		self.faviconClause = self.getFaviconClause ('http://' + self.domainName + '/favicon.ico')
		self.LoginResponsePage = FrameLoginResponsePage
		self.LogoutResponsePage = FrameLogoutResponsePage

		self.urlPatterns = [
			['', StaticPage, 'index'],
			['+', StaticPage],
			# ['downloads/*', RestrictedStaticPage],
			['test/*', DynamicTestPage],
		]

	def __call__ (self, environ, start_response):
		if environ ['PATH_INFO'] .strip () .lower () .split ('.') [-1] in ('/', 'html', 'zip'):
			referrer = 'ip: {}, {} --> {}{}'.format (
				environ ['HTTP_X_FORWARDED_FOR'] if 'HTTP_X_FORWARDED_FOR' in environ else environ ['REMOTE_ADDR'],
				environ ['HTTP_REFERER'] if 'HTTP_REFERER' in environ else 'browser',
				environ ['HTTP_HOST'],
				environ ['PATH_INFO']
			)
			self.log (referrer, context = 'access')
				
		return super () .__call__ (environ, start_response)
		
# If name == '__main__' a test server will be instantiated
# If it isn't, so site.py is a module rather than a main program, the production server will do it's job
# Further explanation in app.py and baseApp.py

application = Site (__file__, __name__)
