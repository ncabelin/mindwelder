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


def createUser(login_session):
	# creates a user via session and returns the user id
	newUser = User(name = login_session['username'],
		email = login_session['email'],
		picture = login_session['picture'])
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email = login_session['email']).one()
	return user.id

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
	posts = [
		{ "subject": "Subject 1",
			"content": "This is content 1",
			"date_modified": "None",
			"user_id": "123"},
		{ "subject": "Subject 2",
			"content": "This is content 2",
			"date_modified": "None",
			"user_id": "134"}
	]
	return render_template('front.html',
		user_logged = None,
		user_id_logged = None,
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

@app.route('/showpost')
def showPost():
	return render_template('showpost.html')

@app.route('/showuser')
def showUser():
	return render_template('showuser.html')

@app.route('/editpost')
def editPost():
	return render_template('editpost.html')



if __name__ == '__main__':
	app.debug = True
	app.secret_key = 'jasdfJakSqa'
	app.run(host='0.0.0.0', port = 15000)