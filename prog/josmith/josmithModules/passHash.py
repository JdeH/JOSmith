import base64
import uuid
import hashlib
 
def hashPassword (password, salt = None):
	if salt is None:
		salt = uuid.uuid4().hex
		
	hashedPassword = hashlib.sha512 (password.encode ('utf-8') + salt.encode ('utf-8')) .hexdigest ()
	return hashedPassword, salt
 
def passwordOk (password, hashedPassword, salt):
	rehashedPassword, salt = hashPassword (password, salt)
	return rehashedPassword == hashedPassword
	