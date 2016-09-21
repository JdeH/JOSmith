class BaseApp:

	# This function is the actual standardized entrypoint that represents the central part of the WSGI spec
	# It is called for each page request
	def __call__ (self, environ, start_response):
		calledPage = self.urlMatcher.callMatching (environ)
		start_response (calledPage.status, calledPage.headers)
		
		if calledPage.encodeAs == None:
			return calledPage.content
		else:
			return [buffer.encode (calledPage.encodeAs) for buffer in calledPage.content]
	
	# This function intantiates and starts a simple, local WSGI testserver that comes with the Python distribution
	# It will called if site.py has module name __main__, so is the main module
	# This is the case if we're testing JOSmith locally by the command 'python site.py', Python version >= 3.5
	# If on the other hand if we use a production WSGI server, it will just call __call__ each time a page request arrives
	
	def serve (self):
		from wsgiref.simple_server import make_server
		print ('Serving on http://{}...'.format (self.domainName))
		domainNameParts = self.domainName.split (':')	# Only makes sense in case of local server
		hostName = domainNameParts [0]
		portNr = int (domainNameParts [1])
		make_server (hostName, portNr, self) .serve_forever ()
		