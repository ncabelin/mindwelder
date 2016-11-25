import re
# form validation functions
# -------------------------

def valid_username(username):
	if username and (len(username) < 30):
		return username
	else:
		return None

def valid_password(password):
	if password and (len(password) > 8):
		return password
	else:
		return None

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
	return email and EMAIL_RE.match(email)
