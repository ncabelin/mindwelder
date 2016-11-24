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
import bleach

app = Flask(__name__)

from sqlalchemy import create_engine, desc
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

def find_post(post_id):
	try:
		post = session.query(Post).filter_by(id = post_id).one()
		return post
	except Exception as e:
		print e
		return None

def find_user_posts(user_id):
	try:
		posts = session.query(Post).filter_by(
			user_id = user_id).order_by(desc(Post.date_added)).all()
		return posts
	except Exception as e:
		print e
		return None

def find_likes_sum(post_id):
	try:
		likes = session.query(Like).filter_by(post_id = post_id).count()
		return likes or 0
	except Exception as e:
		print e
		return None

def find_like(post_id):
	try:
		user = find_logged_user()
		like = session.query(Like).filter_by(post_id = post_id).filter_by(
			user_id = user.id).one()
		return like
	except Exception as e:
		print e
		return None

def find_comments(post_id):
	try:
		comments = session.query(Comment).filter_by(
			post_id = post_id).order_by(desc(Comment.date_added)).all()
		return comments
	except Exception as e:
		print e
		return None

def find_comment(comment_id, post_id):
	try:
		comment = session.query(Comment).filter_by(
			id = comment_id).filter_by(post_id = post_id).one()
		return comment
	except Exception as e:
		print e
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

def imgurcheck(link):
	if (link[:19] == 'http://i.imgur.com/') and (len(link) < 35):
		return link
	else:
		return ''

def find_username(user_id):
	user = getUserByID(user_id)
	return user.username

app.jinja_env.filters['standard_date'] = standard_date
app.jinja_env.filters['firstline'] = firstline
app.jinja_env.filters['markdown'] = markdown
app.jinja_env.filters['find_username'] = find_username
app.jinja_env.filters['find_likes_sum'] = find_likes_sum
app.jinja_env.filters['imgurcheck'] = imgurcheck

google_client_id = json.loads(
		open('client_secret_mw.json', 'r').read()
	)['web']['client_id']

@app.route('/', methods=['GET'])
def showFront():
	# public facing page render
	page = request.args.get('page')
	if not page:
		page = 0
	else:
		page = int(page)

	offset_num = page * 10
	user = find_logged_user()
	posts = session.query(Post).order_by(desc(
		Post.date_added)).offset(offset_num).limit(10).all()
	return render_template('front.html',
		user_logged = user,
		posts = posts,
		page_number = page)

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

@app.route('/fbconnect', methods = ['GET', 'POST'])
def fbconnect():
	# Facebook Oauth2 connection
	if request.args.get('state') != login_session['state']:
		return respond('Error', 401)

	access_token = request.data

	app_id = json.loads(open('fbclient_secret.json',
		'r').read())['web']['app_id']
	app_secret = json.loads(open('fbclient_secret.json',
		'r').read())['web']['app_secret']

	url = ('https://graph.facebook.com/oauth/access_token?grant_type='
		'fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' 
				% (app_id, app_secret, access_token))

	h = httplib2.Http()
	result = h.request(url, 'GET')[1]

	# strip expire tag from access token
	token = result.split("&")[0]
	
	url = ('https://graph.facebook.com/v2.4/me?%s'
		'&fields=name,id,email' % token)
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]

	data = json.loads(result)

	login_session['provider'] = 'facebook'
	login_session['username'] = data['name']
	login_session['email'] = data['email']
	login_session['facebook_id'] = data['id']
	login_session['access_token'] = token

	# get user picture in a separate call
	url = ('https://graph.facebook.com/v2.4/me/picture?%s'
		'&redirect=0&height=200&width=200' % token)
	h = httplib2.Http()
	result = h.request(url, 'GET')[1]
	data = json.loads(result)
	login_session['picture'] = data['data']['url']

	# see if user exists by email
	user_id = getUserID(login_session['email'])
	if not user_id:
		user_id = createUser(login_session, 'facebook')
	login_session['user_id'] = user_id

	return ('You are now logged in as %s' % login_session['username'])

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
			flash('Logged out using Google+')
			return redirect(url_for('showFront'))
		else:
			return respond('Failed to revoke token for given user.', 404)

	elif login_session['provider'] == 'facebook':
		facebook_id = login_session['facebook_id']
		access_token = login_session['access_token']
		url = ('https://graph.facebook.com'
			'/%s/permissions?access_token=%s' % (facebook_id,access_token))
		h = httplib2.Http()
		result = h.request(url, 'DELETE')[1]
		session_list = ['facebook_id',
			'username',
			'email',
			'picture',
			'user_id',
			'access_token']
		for s in session_list:
			del login_session[s]
		flash('Logged out using Facebook')
		return redirect('/')

	else:
		return redirect(url_for('login'))


@app.route('/addpost', methods=['GET', 'POST'])
@login_required
def addPost():
	user = getUserByEmail(login_session['email'])
	if user:
		# POST method add category
		if request.method == 'POST':
			post = Post(title = request.form['title'],
				user_id = user.id,
				picture = request.form['picture'],
				post_content = request.form['content'],
				keywords = request.form['keywords'],
				date_added = datetime.datetime.now(),
				)
			session.add(post)
			session.commit()
			return redirect(url_for('showUser',
				user_id = user.id))

		# GET method shows add page
		return render_template('addpost.html',
			user_logged = user)
	else:
		return redirect(url_for('login'))

@app.route('/showpost/<int:post_id>', methods=['GET'])
def showPost(post_id):
	post = find_post(post_id)
	comments = find_comments(post_id)
	if post:
		return render_template('showpost.html',
			post = post,
			comments = comments,
			user_logged = find_logged_user())
	else:		
		return render_template('error.html', message = 'Post not found')

@app.route('/showpostcomment/<int:post_id>/<int:comment_id>', methods=['GET'])
@login_required
def showPostComment(post_id, comment_id):
	post = find_post(post_id)
	comments = find_comments(post_id)
	comment = find_comment(comment_id, post_id)
	user = find_logged_user()
	if post and comment:
		if comment.user_id == user.id:
			return render_template('showpost.html',
				post = post,
				comments = comments,
				comment = comment,
				user_logged = find_logged_user())
		else:
			print 'what the fuck man 1'
			return render_template('error.html', message = 'Not authorized')
	else:		
		print 'what the fuck man 2'
		return render_template('error.html', message = 'Post not found')	

@app.route('/editpost/<int:post_id>', methods=['GET', 'POST'])
@login_required
def editPost(post_id):
	user = find_logged_user()
	post = find_post(post_id)
	if user.id == post.user_id:

		# POST method edit 
		if request.method == 'POST':
			post.title = request.form['title']
			post.post_content = request.form['post_content']
			post.date_added = datetime.datetime.now()
			post.keywords = request.form['keywords']
			session.add(post)
			session.commit()
			return redirect(url_for('showPost', post_id = post_id))

		# GET method
		return render_template('editpost.html',
			user_logged = user,
			post = post)

	else:
		return render_template('error.html',
			message = 'Not authorized to edit this post')

@app.route('/deletepost/<int:post_id>', methods=['POST'])
@login_required
def deletePost(post_id):
	user = getUserByEmail(login_session['email'])
	post = find_post(post_id)
	if user and post:
		# check ownership
		if user.id == post.user_id:
			# POST method to delete
			if request.method == 'POST':
				session.delete(post)
				session.commit()
				return redirect(url_for('showUser', user_id = user_id))
		else:
			return render_template('error.html',
				message = 'Not authorized to delete this post')
	else:
		return render_template('error.html',
			message = 'Post not found')

@app.route('/showuser/<int:user_id>', methods = ['GET'])
def showUser(user_id):
	posts = find_user_posts(user_id)
	return render_template('showuser.html', 
		posts = posts,
		user_logged = find_logged_user(),
		user = getUserByID(user_id))

@app.route('/likepost/<int:post_id>', methods=['POST'])
@login_required
def likePost(post_id):
	user = find_logged_user()
	like = find_like(post_id)
	if like:
		flash('Cannot like a post more than once')
		return redirect('/showpost/%s#likes' % post_id)
	else:
		like = Like(post_id = post_id, user_id = user.id)
		session.add(like)
		session.commit()
		return redirect('/showpost/%s#likes' % post_id)

@app.route('/addcomment/<int:post_id>', methods=['POST'])
@login_required
def addComment(post_id):
	user = find_logged_user()
	post = find_post(post_id)
	comment = Comment(user_id = user.id,
		post_id = post.id,
		content = request.form['content'],
		date_added = datetime.datetime.now()
		)
	session.add(comment)
	session.commit()
	return redirect('/showpost/%s#comments' % post_id)

@app.route('/editcomment/<int:post_id>/<int:comment_id>', methods=['POST'])
@login_required
def editComment(post_id, comment_id):
	user = find_logged_user()
	post = find_post(post_id)
	comment = find_comment(comment_id, post_id)
	if post and comment:
		# check ownership
		if comment.user_id == user.id:
			comment.content = request.form['content']
			session.add(comment)
			session.commit()
			return redirect('/showpost/%s#comments' % post_id)
		else:
			return render_template('error.html',
				message = 'Not authorized to edit comment')
	else:
		return render_template('error.html',
			message = 'Post / Comment not found')

@app.route('/deletecomment/<int:post_id>/<int:comment_id>', methods=['POST'])
@login_required
def deleteComment(post_id, comment_id):
	user = find_logged_user()
	post = find_post(post_id)
	comment = find_comment(comment_id, post_id)
	if post and comment:
		# check ownership
		if comment.user_id == user.id:
			session.delete(comment)
			session.commit()
			return redirect('/showpost/%s#comments' % post_id)
		else:
			return render_template('error.html',
				message = 'Not authorized to delete comment')
	else:
		return render_template('error.html',
			message = 'Post / Comment not found')


if __name__ == '__main__':
	app.debug = True
	app.secret_key = secret()
	app.run(host='0.0.0.0', port = 15000)