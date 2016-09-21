import sys
import traceback
import urllib
import datetime

app = None
cs = None

class Log:
	def __init__ (self, application, context = 'general'):
		self.application = application
		self.contexts = []
		self.pushContext (context)
				
	def pushContext (self, context):
		self.contexts.append (context)
		
	def popContext (self):
		self.contexts.pop ()
		
	def getContext (self):
		return self.contexts [-1]
		
	def __call__ (self, *args, context = None, lead = '', trail = '\n'):
		if context:
			self.pushContext (context)
		
		if app.logToFile:
			try:
				file = open (self.application.logFileNameTemplate.format (str (datetime.datetime.now ())[:7]), 'a')
			except:	# Just in case logFileNameTemplate not yet ready or faulty
				file = sys.stdout
		else:
			file = sys.stdout
		
		file.write (lead)
		file.write (app.domainName + ': ' + str (datetime.datetime.now ()) [:19] + ' [' + self.getContext () + ']')
		file.writelines ([' ' + str (arg) for arg in args])
		file.write (trail)
		
		if app.debug:
			try:
				trace = traceback.format_exc ()
				file.write ('BEGIN DEBUG INFO\n')
				file.write (trace)
				file.write ('END DEBUG INFO\n\n')
			except:	# No exception, just a regular log
				pass
		
		if file != sys.stdout:	# Don't close stdout, since it will then cease accepting data
			file.close ()
			
		if context:
			self.popContext ()
			
def getFullUrl (environ):	# ... Currently unused
	url = environ ['wsgi.url_scheme'] + '://'

	if environ.get ('HTTP_HOST'):
		url += environ ['HTTP_HOST']
	else:
		url += environ ['SERVER_NAME']

		if environ ['wsgi.url_scheme'] == 'https':
			if environ ['SERVER_PORT'] != '443':
			   url += ':' + environ ['SERVER_PORT']
		else:
			if environ ['SERVER_PORT'] != '80':
			   url += ':' + environ ['SERVER_PORT']

	url += urllib.parse.quote (environ.get('SCRIPT_NAME', ''))
	url += urllib.parse.quote (environ.get('PATH_INFO', ''))
	if environ.get ('QUERY_STRING'):
		url += '?' + environ ['QUERY_STRING']
		
	return url