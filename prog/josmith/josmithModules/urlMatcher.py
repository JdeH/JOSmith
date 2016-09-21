import datetime
import copy
import traceback

import util
import basePages

class UrlMatcher:
	def __init__ (self, app):
		self.app = app
		
	def getUrlPatterns (self):
		# Split URL part of URL patterns in chunks on /
		self.urlPatterns = [[[chunk for chunk in urlPattern [0] .split ('/') if chunk]] + list (urlPattern [1:]) for urlPattern in self.app.urlPatterns]
			
	def callMatching (self, environ):
		try:
			# Also split actual URL in chunks, so it can be easily compared against the URL part of the current URL pattern
			
			url = [chunk for chunk in environ ['PATH_INFO'].lower () .split ('/') if chunk]

			# We now set out to find the best matching URL pattern
			#
			# The best URL pattern is the pattern that
			#	Condition 1: Has the same nr of chunks as the actual URL
			#   Condition 2: Has no chunks that contradict the actual URL
			#	Condition 3: Starts with the largest number of exactly matching (non parameter) chunks (do not have to be adjacent)
			#
			# Wildcards denote parameters to be supplied to pages, rather than the pages themselves
			#	?[name] matches 1 chunk
			#	+ matches 1 or more chunks
			#	* matches 0 or more chunks
						
			bestMatchLength = -1
			bestMatch = []
			
			bestUrlPattern = None
			for urlPattern in self.urlPatterns:
			
				# If URL part of the URL pattern ends on * or +
				if urlPattern [0] and urlPattern [0][-1] in ('*', '+'):
				
					# Make a copy of it
					# urlPattern = copy.deepcopy (urlPattern)
					urlPattern = [copy.deepcopy (urlPattern [0])] + urlPattern [1:]	# ??? Why is a copy of the tail needed
					
					# Remove the * or +
					popped = urlPattern [0] .pop ()
					
					# If it was a +
					if popped == '+':					# One or more chunks
						# Replace it by at least one ?
						urlPattern [0] .append ('?')
						
					# If was a * or a + and the URL part of the copied URL pattern isn't yet long enough
					if len (urlPattern [0]) < len (url):
						# Add the required nr of ?'s to make it long enough
						urlPattern [0] += (len (url) - len (urlPattern [0])) * ['?']
					
				# If after replacing an eventual trailing * or + by the most appropriate nr of ?'s, its doesn't have right length
				if len (urlPattern [0]) != len (url):	# Condition 1
					# Continue to the next URL pattern, since the current one doesn't fit
					continue
				
				# Now we have 2 equally long lists of things to match, let's start matching
				match = []
				for chunkPair in zip (urlPattern [0], url):
				
					# If the chunks in the current chunkPair match each other exactly
					if chunkPair [0] == chunkPair [1]:	# Exactly matching chunk as in condition 3
						# Append the chunk to the list of exactly matching chunks, the longest list is said to represent the best match, so wins
						match.append (chunkPair [1])
						
					# If the chunks in the current chunkPar don't match, but there's a ? in the pattern, the pattern is still valid 
					elif chunkPair [0] .startswith ('?'):			# Condition 2 still satisfied
						# Proceed to next chunk of same pattern
						pass
						
					# If the chunks don't match and the reference chunk also isn't a wildcard (?) then the pattern is invalid
					else:								# Condition 2 violated so reject pattern
						# Abandon this pattern
						break
				else:									# No break seen, so pattern not rejected
					# If it matches better than any previous pattern tried
					if len (match) > bestMatchLength:	# Evaluate condition 3
					
						# Store its characteristics
						bestMatchLength = len (match)
						bestMatch = match
						bestUrlPattern = urlPattern
			
			# If no pattern matches at all
			if bestUrlPattern == None:					# All patterns rejected
				# Sound the alarm
				raise Exception ('No matching URL pattern found')
					
			# Having found the best matching URL pattern, now we will compare it to the actual url to find out what the parameters are
			
			args = []
			kwargs = {}
			
			# First we zip them together
			for chunkPair in zip (bestUrlPattern [0], url):
				# If the reference pattern chunk is a wildcard
				if chunkPair [0] .startswith ('?'):
					# If it's only a ? it has no name
					if len (chunkPair [0]) == 1:
						# So it's an arg rather than a kwarg
						args.append (chunkPair [1])
					else:
						# If it has a name it's a kwarg
						kwargs [chunkPair [0][1:]] = chunkPair [1]
					
			# Fixed args are elements of the referene pattern from and including the 2nd one
			# They're always passed as first elements in the args parameter of the constructor of the page class
			# So effectively it is as if they were passed in as part of the URL matching anonymous wildcards
			# In other words, they seem part of the actual page URL
			fixedArgs = bestUrlPattern [2:]
			
			return bestUrlPattern [1] (environ, tuple (bestMatch), *(fixedArgs + args), **kwargs)	# May raise exception
		except:
			return basePages.NotFoundPage (environ, None, stacktrace = traceback.format_exc ())
