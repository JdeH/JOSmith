import os
import http.cookies
import mimetypes
import codecs
import random
import urllib

import util

class Kwargs:
	pass

class Page:
	def __init__ (self, environ, match, *args, **kwargs):
		self.environ = environ
		self.match = match
		self.args = args
		self.kwargs = Kwargs ()
		
		for key in kwargs:
			setattr (self.kwargs, key, kwargs [key])
			
		self.params = {}
		try:
			body = str (self.environ ['wsgi.input'] .read (int (self.environ ['CONTENT_LENGTH'])), encoding = 'utf8')
			
			if self.environ ['CONTENT_TYPE'] == 'application/json':
				self.json = body
			else:
				paramPairs = body.split ('&')

				for paramPair in paramPairs:
					paramPair = paramPair.split ('=')
					self.params [urllib.parse.unquote_plus (paramPair [0] .strip ())] = urllib.parse.unquote_plus (paramPair [1] .strip ())
		except Exception as e:
			pass

		self.app = util.app
		self.cs = util.app.cs
		
		self.allowedRoleNames = []
		self.allowedUserEmailAddresses = []
		
		self.config ()
		self.check ()
		
	def config (self):
		pass
		
	def check (self):
		ok = not (self.allowedRoleNames or self.allowedUserEmailAddresses)
		self.user = None
		self.userRoles = []
				
		if 'HTTP_COOKIE' in self.environ:
			try:
				cookie = http.cookies.SimpleCookie()
				cookie.load (self.environ ['HTTP_COOKIE'])
				token = cookie [self.app.cookieName] .value
				
				# Get user data for any later use
				self.user = self.cs.execute ('one', 'SELECT id, email_address FROM users WHERE token == "{}"'.format (token))
				
				if self.user:	# Not logged out
					# Get role data for any later use
					userIdsRoleIds = self.cs.execute ('all', 'SELECT role_id FROM users_roles WHERE user_id == {}'.format (self.user ['id']))
					
					for userIdRoleId in userIdsRoleIds:
						self.userRoles.append (self.cs.execute ('one', 'SELECT name FROM roles WHERE id == {}'.format (userIdRoleId ['role_id'])))
						
					# Use user data and roles to check authorisation				
					if self.user ['email_address'] in self.allowedUserEmailAddresses:
						ok = True
						
					if not ok:
						for userRole in self.userRoles:
							if userRole ['name'] in self.allowedRoleNames:
								ok = True
								break
			except:	# Hack for Google Analytics
				pass
							
		self.get () if ok else self.getRedirectToLogin ()
		
	def getCommon (self):
		self.status = '200 OK'
		self.headers = [('content-type', 'text/html')]
		self.encodeAs = 'utf-8'
		
	def get (self):
		self.getCommon ()
		self.content = ['Empty page']
		
	def getRedirectToLogin (self):
		self.getCommon ()	
		self.content = [self.app.getHtmlClause (self.app.getRedirectClause ('/{}{}'.format (self.app.loginUrl, self.environ ['PATH_INFO'])))]
		
class NotFoundPage (Page):
	def get (self):
		super () .get ()
		
		self.status = '404 Not Found'
		self.content = ['Page cannot be found']
	
		if hasattr (self.kwargs, 'stacktrace'):
			self.app.log (self.kwargs.stacktrace)
			if self.app.debug:
				self.content += ['<pre>' + self.kwargs.stacktrace + '</pre>']	

class StaticPage (Page):
# A static page doesn't have parameters, although the url may have args and the page itself may be a pyhtml file.
# The URL including args just denotes a path rooted in the static directory.
# To use parameters, derive a dynamic page class from class Page.

	contentTypes = {
		'pyhtml':	'text/pyhtml',
		'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
		'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
		'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
	}

	def get (self):
		super () .get ()
		
		originalFilePathTail = '/'.join (self.match + self.args)
		filePath = self.app.staticDirName + '/' + originalFilePathTail
		notFoundException = Exception ('Static file or dir not found: {0}'.format (filePath))
		
		clairvoyant = (
			self.app.forceClairvoyant or
			len (set ([userRole ['name'] for userRole in self.userRoles]) & set ((self.app.superUserRoleName, self.app.clairUserRoleName))) > 0
		)
		
		for arg in self.args:
			print (111, arg, 222)
			if arg.startswith ('_') and not clairvoyant and not arg in self.app.clairChunks:
				raise notFoundException	# Requests to URL's containing a chunk starting with '_' are blocked
												
		if os.path.isdir (filePath):
			if os.path.isfile (filePath + '/_') or clairvoyant:# Only dirs containing a file named '_' are browsable
				all = [name for name in os.listdir (filePath) if (not name.startswith ('_') or clairvoyant)]	# Files or dirs starting with '_' are invisible
				parentDirs = ['..'] if (os.path.isfile (filePath + '/../_') or clairvoyant) else [] 
				dirs = sorted (parentDirs + [name for name in all if os.path.isdir (filePath + '/' + name)])
				files = sorted ([name for name in all if os.path.isfile (filePath + '/' + name)])
				self.content = (
					['<h4>Dirs:<br></h4>'] +
					['<a href=/{0}/{1}>{1}</a><br>'.format (originalFilePathTail, anEntry) for anEntry in dirs] +
					['<h4>Files:<br></h4>'] +
					['<a href=/{0}/{1}>{1}</a><br>'.format (originalFilePathTail, anEntry) for anEntry in files]
				)
			else:
				raise notFoundException
		else:
			try:
				if not os.path.isfile (filePath):
					originalFilePath = filePath
					filePath = originalFilePath + '.html'
					
				if not os.path.isfile (filePath):
					filePath = originalFilePath + '.pyhtml'
					
				if os.path.isfile (filePath):
					rawContentType = self.guessType (filePath)
						
					if rawContentType in ('text/html', 'text/pyhtml'):
						aFile = codecs.open (filePath, 'r', encoding = 'utf-8')
					else:
						self.encodeAs = None
						aFile = open (filePath, 'rb')
						
					rawContent = aFile.read ()
					aFile.close ()
					
					if rawContentType == 'text/pyhtml':
						self.headers = [('content-type', 'text/html')]
						self.encodeAs = None
						cookedContent = 'def execute (self):\n\t' + rawContent.replace ('\r', '\n') .replace ('\n', '\n\t') + '\nself.executor = execute'
						exec (cookedContent)
						self.executor (self)
						# The executor hack is needed to make globals in a pyhtml script accessible in list comprehensions
						# Actually they become locals to the executor
						self.content = [self.content.encode ('utf-8-sig')]
					else:
						self.headers = [('content-type', rawContentType)]		
						self.content = [rawContent]
						
			except Exception as e:
				raise notFoundException
		
	def guessType (self, filePath):
		extension = filePath.split ('.')[-1]
		if extension in type (self) .contentTypes:
			return type (self) .contentTypes [extension]
		
		contentType, encoding = mimetypes.guess_type (filePath)
		if contentType:
			return contentType
			
		return 'text/plain'
	
class LoginPage (Page):
	def get	(self):
		super () .get ()
	
		self.content = [self.app.getHtmlClause (
			head = '''
				<style type="text/css">
					.caption {margin-bottom: 20px;}

					.email_address_label {display: inline-block; width: 100;}
					.email_address_field {display: inline-block; width: 200;}
					
					.password_label {display: inline-block; width: 100;}
					.password_field {display: inline-block; width: 200;}
					
					.submit {width: 100; margin-top: 20px;}
				</style>
			''',
			body = '''
				<form action = "/{}/{}" method = "post">
					<div class = "caption">Please log in</div>
					
					<div email_address_group>
						<div class = "email_address_label">Email address:</div>
						<input type = "text" name = "email_address" value = "" maxlength = "200" class = "email_address_field" />
					</div>
					
					<div password_group>
						<div class = "password_label">Password:</div>
						<input type = "password" name = "password" value = "" maxlength = "200" class = "password_field" />
					</div>
					
					<input type = "submit" value="Submit" class = "submit"/>
				</form>
			'''.format (self.app.loginResponseUrl, '/'.join (self.args))
		)]

class LoginResponsePage (Page):	# This page contains a cookie to grant access, and then it redirects to the target url
	def get (self):
		super () .get ()
		
		fetched = None
		
		try:
			token = random.random ()
			cookie = http.cookies.SimpleCookie()
			cookie [util.app.cookieName] = token
			
			cookie [util.app.cookieName]['Path'] = '/'
			fetched = self.cs.execute ('one', 'SELECT id, password FROM users WHERE email_address = "{}"'.format (self.params ['email_address']))
		except Exception as exception:
			pass
			
		if fetched and self.params ['password'] == fetched ['password']:
			self.cs.execute ('UPDATE users SET token = "{}" WHERE id = {}'.format (token, fetched ['id']))
			fetched = self.cs.execute ('one', 'SELECT * FROM users WHERE id = 1')
			
			self.headers += [('Set-Cookie', morsel.OutputString ()) for morsel in cookie.values ()]
			self.content = [util.app.getHtmlClause (self.app.getRedirectClause ('/' + '/'.join (self.args)))]
		else:
			raise Exception ('Combination of email address and password unknown')
			
class LogoutResponsePage (Page):	# Always redirects
	def get (self):
		super () .get ()
		
		cookie = http.cookies.SimpleCookie()
		cookie.load (self.environ ['HTTP_COOKIE'])
		token = cookie [self.app.cookieName] .value
		self.cs.execute ('UPDATE users SET token = "" WHERE token == "{}"'.format (token))
		
		self.content = [util.app.getHtmlClause (self.app.getRedirectClause ('/' + '/'.join (self.args)))]
				
				