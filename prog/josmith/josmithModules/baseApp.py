class BaseApp:
	def __call__ (self, environ, start_response):
		calledPage = self.urlMatcher.callMatching (environ)
		start_response (calledPage.status, calledPage.headers)
		
		if calledPage.encodeAs == None:
			return calledPage.content
		else:
			return [buffer.encode (calledPage.encodeAs) for buffer in calledPage.content]
		
	def serve (self):
		from wsgiref.simple_server import make_server
		print ('Serving on http://{}...'.format (self.domainName))
		domainNameParts = self.domainName.split (':')	# Only makes sense in case of local server
		hostName = domainNameParts [0]
		portNr = int (domainNameParts [1])
		make_server (hostName, portNr, self) .serve_forever ()
		