import traceback
import sqlite3
import threading

class LockableCursor:
	def __init__ (self, cursor):
		self.cursor = cursor
		self.lock = threading.Lock ()
				
	def execute (self, arg0, arg1 = None):
		self.lock.acquire ()
		
		try:
			self.cursor.execute (arg1 if arg1 else arg0)
			
			if arg1:
				if arg0 == 'all':
					result = self.cursor.fetchall ()
				elif arg0 == 'one':
					result = self.cursor.fetchone ()
		except Exception as exception:
			raise exception
			
		finally:
			self.lock.release ()
			if arg1:
				return result

def dictFactory (cursor, row):
	aDict = {}
	for iField, field in enumerate (cursor.description):
		aDict [field [0]] = row [iField]
	return aDict
				
class Db:
	def __init__ (self, app):
		self.app = app
		
	def connect (self):
		self.connection = sqlite3.connect (self.app.dbFileName, check_same_thread = False, isolation_level = None)	# Will create db if nonexistent
		self.connection.row_factory = dictFactory
		self.cs = LockableCursor (self.connection.cursor ())
		
		if self.app.authorize:
			try:
				self.createSuperUser ()
			except: # Assume authorization tables and super user already exist
				pass
			
		return self.cs
		
	def createSuperUser (self):
		self.app.log.pushContext ('initialization')
		try:
			# Create users table and insert default user
			self.cs.execute ('CREATE TABLE users (id INTEGER PRIMARY KEY, email_address, password, token)')			
			self.cs.execute ('INSERT INTO users (email_address, password) VALUES ("{}", "{}")'.format (self.app.defaultUserEmailAddress, self.app.defaultUserPassword))
			
			# Create roles table and insert default role
			self.cs.execute ('CREATE TABLE roles (id INTEGER PRIMARY KEY, name)')
			self.cs.execute ('INSERT INTO roles (name) VALUES ("{}")'.format (self.app.defaultRoleName))
			
			# Create users_roles table and assign default role to default user
			self.cs.execute ('CREATE TABLE users_roles (id INTEGER PRIMARY KEY, user_id, role_id)')	

			defaultUserId = self.cs.execute ('one', 'SELECT id FROM users WHERE email_address = "{}"'.format (self.app.defaultUserEmailAddress)) ['id']			
			defaultRoleId = self.cs.execute ('one', 'SELECT id FROM roles WHERE name = "{}"'.format (self.app.defaultRoleName)) ['id']
			
			self.cs.execute ('INSERT INTO users_roles (user_id, role_id) VALUES ({}, {})'.format (defaultUserId, defaultRoleId))
			
			self.app.log ('authorization tables created and root super user inserted')
		except Exception as exception:
			self.app.log (str (exception))
		finally:
			self.app.log.popContext ()
			