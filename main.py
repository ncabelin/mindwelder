from flask import (Flask,
	render_template,
	request,
	url_for,
	redirect,
	flash,
	jsonify)
from flask import session as login_session
from flask import make_response
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import datetime
from functools import wraps
from secretkeys import secret

app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, User, Post, Like, Comment

engine = create_engine('sqlite:///mindwelder.db')
DBSession = sessionmaker(bind = engine)
session = DBSession()

def respond(msg, err):
	res = make_response(json.dumps(msg), err)
	res.headers['Content-Type'] = 'application/json'
	return res

# user functions
# --------------
def getUserByEmail(email):
	try:
		user = session.query(User).filter_by(email = email).one()
		return user
	except:
		return None

def getUserID(email):
	try:
		user = session.query(User).filter_by(email = email).one()
		return user.id
	except:
		return None

def getUserByID(user_id):
	user = session.query(User).filter_by(id = user_id).one()
	return user

def createUser(login_session, account):
	# creates a user via session and returns the user id
	newUser = User(username = login_session['username'],
		email = login_session['email'],
		account = account,
		picture = login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email = login_session['email']).one()
	return user.id

def find_logged_user():
	# function that checks if a user is logged in first
	# and returning the user object, only used in dual public/private facing routes
	if 'username' in login_session:
		return getUserByEmail(login_session['email'])
	else:
		return None

def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if 'username' in login_session:
			return f(*args, **kwargs)
		else:
			return redirect(url_for('login'))
	return decorated_function

# jinja2 filters
# --------------
def firstline(content):
	return content.split('\n')[0]

def standard_date(date):
	return date.strftime('%b %d, %Y')

def markdown(content):
    bleached_content = bleach.clean(content,
        tags = ['strong','b','i','em','h1','h2','pre','code', 'br', 'u', 'li', 'ul', 'ol'])
    c = bleached_content.split('\n')
    # first line (description) will be a bigger font size
    c[0] = '<h3>%s</h3>' % c[0]
    content = '\n'.join(c)
    content = content.replace('\n', '<br>')
    return content

app.jinja_env.filters['standard_date'] = standard_date
app.jinja_env.filters['firstline'] = firstline
app.jinja_env.filters['markdown'] = markdown

google_client_id = json.loads(
		open('client_secret_mw.json', 'r').read()
	)['web']['client_id']

@app.route('/', methods=['GET'])
def showFront():
	# public facing page render
	user = find_logged_user()
	posts = session.query(Post).all()
	# posts = [
	# 	{ "subject": "Subject 1",
	# 		"content": "This is content 1",
	# 		"date_modified": "None",
	# 		"user_id": "123"},
	# 	{ "subject": "Subject 2",
	# 		"content": "This is content 2",
	# 		"date_modified": "None",
	# 		"user_id": "134"}
	# ]
	return render_template('front.html',
		user_logged = user,
		posts = posts,
		page_number = 1)

@app.route('/login', methods = ['GET', 'POST'])
def login():
	state = ''.join(random.choice(string.ascii_uppercase + 
		string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', state = state)

@app.route('/gconnect', methods = ['POST'])
def gconnect():
	if request.args.get('state') != login_session['state']:
		return respond('Invalid state parameter', 401)

	code = request.data
	print(code)

	try:
		oauth_flow = flow_from_clientsecrets('client_secret_mw.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code).to_json()
	except FlowExchangeError:
		return respond('Failed to upgrade the authorization code', 401)

	access_token = json.loads(credentials)['access_token']
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' 
		% access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])

	if result.get('error') is not None:
		return respond(result.get('error'), 500)

	gplus_id = json.loads(credentials)['id_token']['sub']
	if result['user_id'] != gplus_id:
		return respond("Token's user ID doesn't match given user ID.", 400)

	if result['issued_to'] != google_client_id:
		return respond("Token's client ID doesn't match app's", 401)

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		return respond("Current user is already connected", 200)

	login_session['credentials'] = credentials
	login_session['gplus_id'] = gplus_id

	userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
	params = { 'access_token': access_token, 'alt': 'json' }
	answer = requests.get(userinfo_url, params = params)

	data = answer.json()

	login_session['provider'] = 'google'
	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

	# see if user exists by email
	user_id = getUserID(login_session['email'])
	if not user_id:
		user_id = createUser(login_session, 'google')
	login_session['user_id'] = user_id

	return 'Logging in as ' + login_session['username'] + '...'

@app.route('/gdisconnect', methods = ['GET', 'POST'])
def gdisconnect():
	if login_session['provider'] == 'google':
		credentials = login_session.get('credentials')
		if credentials is None:
			return respond('Current user not connected', 401)

		access_token = json.loads(credentials)['access_token']

		url = ('https://accounts.google.com/o/'
			'oauth2/revoke?token={}'.format(access_token))
		h = httplib2.Http()
		result = h.request(url, 'GET')[0]
		print(result['status'])
		print result

		if result['status'] == '200' or result['status'] == '400':
			session_list = ['credentials',
				'gplus_id',
				'username',
				'email',
				'picture',
				'user_id']
			for s in session_list:
				del login_session[s]
			return redirect(url_for('login'))
		else:
			return respond('Failed to revoke token for given user.', 404)

@app.route('/showpost/<int:post_id>', methods=['GET'])
def showPost(post_id):
	return render_template('showpost.html')

@app.route('/editpost/<int:post_id>', methods=['GET', 'POST'])
def editPost(post_id):
	return render_template('editpost.html')

@app.route('/deletepost/<int:post_id>', methods=['POST'])
def deletePost(post_id):
	return redirect(url_for('showUser', user_id = user_id))

@app.route('/showuser/<int:user_id>')
def showUser(user_id):
	return render_template('showuser.html')

@app.route('/likepost/<int:post_id>', methods=['POST'])
def likePost(post_id):
	return redirect(url_for('showpost', post_id = post_id))

@app.route('/addcomment/<int:post_id>', methods=['POST'])
def addComment(post_id):
	return render_template('addcomment')


if __name__ == '__main__':
	app.debug = True
	app.secret_key = secret()
	app.run(host='0.0.0.0', port = 15000)