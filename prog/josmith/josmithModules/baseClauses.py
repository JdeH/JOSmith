class BaseClauses:
	def getScriptClause (self, url = '', code = ''):
		aType = 'text/javascript'
		if url:
			if code:
				raise Exception ('Script clause with both url and code')
			else:
				return '<script src="{}" type="{}"></script>'.format (url, aType)
		else:
			return '''
				<script type="{}">
					{}
				</script>
			'''.format (aType, code)
					
	def getRedirectClause (self, url):
		return '<meta http-equiv="refresh" content="0; url={}" />'.format (url)
		
	def getHtmlClause (self, head = '', body = ''):
		return '''
			<html>
				<head>
					{}
				</head>
				<body>
					{}
				</body>
			</html>
		'''.format (head, body)
		
	def getFaviconClause (self, url):
		return '<link rel="shortcut icon" type="image/x-icon" href="{}">'.format (url)
		