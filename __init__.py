# TO DO:
# fix html view keywords
# add forgot password, use gmail to send activate
# add flask recaptcha during registration
# add post setting to private, public
# add capability to copy, make setting private instantly
# add title icon

import random, string, datetime, os

# 3rd party modules
from flask import (Flask,
	render_template,
	request,
	url_for,
	redirect,
	flash,
	jsonify)
from flask import session as login_session
from flask import make_response
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
from functools import wraps
import bleach
from bcrypt import hashpw, checkpw, gensalt

app = Flask(__name__)

from sqlalchemy import create_engine, desc, or_
from sqlalchemy.orm import sessionmaker
from database import Base, User, Post, Like, Comment, Keyword, Test

engine = create_engine('postgresql://meeska:Marcopupu2014@localhost:5432/mindwelderdb')
DBSession = sessionmaker(bind = engine)
session = DBSession()

# internal modules
from validators import valid_username, valid_email, valid_password
from parser import markdown
from secretkeys import secret

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

def get_user_pic(user_id):
	user = session.query(User).filter_by(id = user_id).one()
	return user.picture

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
	# and returning the user object with session values
	if 'username' in login_session:
		user = User(id = login_session['user_id'],
			username = login_session['username'],
			picture = login_session['picture'],
			email = login_session['email'],
			account = login_session['provider']
			)
		return user
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

def find_keywords(post_id):
	try:
		keywords = session.query(Keyword).filter_by(
			post_id = post_id).all()
		return keywords
	except Exception as e:
		print e
		return None

def find_posts_by_key(word):
	try:
		# TO DO :
		# refactor to use SQL in a join
		post_ids = session.query(Keyword).filter_by(
			word = word).group_by(Keyword.post_id).all()
		for post in post_ids:
			print post.post_id
		posts = []
		for p in post_ids:
			post = session.query(Post).filter_by(
				id = p.post_id).one()
			posts.append(post)
		for p in posts:
			print post.user_id
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

def find_description(user_id):
	try:
		user = session.query(User).filter_by(id = user_id).one()
		if user.description:
			return user.description
		else:
			return ''
	except Exception as e:
		print e
		return ''

def find_test(post_id, user_id):
	try:
		tests = session.query(Test).filter_by(
			user_id = user_id).filter_by(post_id = post_id).all()
		if tests:
			return tests
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
app.jinja_env.filters['get_user_pic'] = get_user_pic
app.jinja_env.filters['find_description'] = find_description

dir_name = os.path.dirname(os.path.abspath(__file__))
gfile = os.path.join(dir_name, 'client_secret_mw.json')
ffile = os.path.join(dir_name, 'fbclient_secret.json')
google_client_id = json.loads(
		open(gfile, 'r').read()
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
		keywords = session.query(Keyword.word).group_by(Keyword.word).all(),
		page_number = page)

@app.route('/login', methods = ['GET', 'POST'])
def login():
	state = ''.join(random.choice(string.ascii_uppercase + 
		string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', state = state)

@app.route('/register', methods = ['GET', 'POST'])
def register():
	if request.method == 'POST':
		username = valid_username(request.form['username'])
		email = request.form['email']
		password = request.form['password']
		verify = request.form['verify']

		# check if 2 passwords match
		if password != verify:
			flash('Passwords do not match')
			return redirect('/register')

		# check if password is not blank or below 8 characters
		password = valid_password(password)

		if not username:
			flash('Username is not valid')
		if not password:
			flash('Password is not valid')
		if not email:
			flash('Email is not valid')

		if getUserByEmail(email):
			flash('Another user has registered with that email, please use another one')
			return redirect('/register')

		if username and valid_email(email) and password:
			newUser = User(
				username = username,
				description = request.form['description'],
				email = email,
				password = hashpw(password.encode('utf-8'), gensalt()),
				picture = '/static/images/generic.png',
				account = 'mindwelder',
				sq_one = request.form['sq_one'],
				sa_one = hashpw(request.form['sa_one'].encode('utf-8'), gensalt())
				)

			try:
				session.add(newUser)
				session.commit()
				flash('Succesfully registered, please log in')
				return redirect('/login')
			except Exception as e:
				print e
				flash('Error connecting to database')
				return render_template('error.html')
		else:
			return redirect('/register')

	else:
		# GET 
		username = request.args.get('u') or ''
		email = request.args.get('e') or ''
		return render_template('register.html',
			username = username,
			email = email)

@app.route('/mconnect', methods = ['POST'])
def mconnect():
	email = request.form['email']
	password = request.form['password']
	try:
		user = session.query(User).filter_by(email = email).one()
		hashed = user.password.encode('utf-8')
		if hashpw(password.encode('utf-8'), hashed) == hashed:
			login_session['user_id'] = user.id
			login_session['description'] = user.description or None
			login_session['provider'] = user.account
			login_session['username'] = user.username
			login_session['picture'] = user.picture
			login_session['email'] = user.email
			flash('User logged in as {}'.format(user.username))
			return redirect('/')
		else:
			flash('Username / Password not valid')
			return redirect(url_for('login'))
	except:
		flash('Username / Password not valid')
		return redirect(url_for('login'))



@app.route('/gconnect', methods = ['POST'])
def gconnect():
	if request.args.get('state') != login_session['state']:
		return respond('Invalid state parameter', 401)

	code = request.data

	try:
		oauth_flow = flow_from_clientsecrets(gfile, scope='')
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

	app_id = json.loads(open(ffile,
		'r').read())['web']['app_id']
	app_secret = json.loads(open(ffile,
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
			return redirect(url_for('login'))
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
		return redirect(url_for('login'))

	elif login_session['provider'] == 'mindwelder':
		session_list = [
			'provider',
			'username',
			'email',
			'picture']
		for s in session_list:
			del login_session[s]
		flash('Logged out')
		return redirect(url_for('login'))

	else:
		return redirect(url_for('login'))

@app.route('/usersettings', methods=['GET','POST'])
@login_required
def userSettings():
	# POST method
	try:
		user = getUserByEmail(login_session['email'])
	except Exception as e:
		print(e)
		flash('Error: {}'.format(e))
		return render_template('error.html')
	if request.method == 'POST':
		user.username = request.form['username']
		user.description = request.form['description']
		user.picture = request.form['picture'] or '/static/images/generic.png'
		session.add(user)
		session.commit()
		flash('Successfully edited user settings')
		return redirect(url_for('showFront'))

	# GET method
	return render_template('usersettings.html',
		user_logged = user)

@app.route('/deleteuser', methods=['GET','POST'])
@login_required
def deleteUser():
	try:
		user = getUserByEmail(login_session['email'])
	except Exception as e:
		print(e)
		flash('Error: {}'.format(e))
		return render_template('error.html')
	if request.method == 'POST':
		session.delete(user)
		session.commit()
		return redirect('/gdisconnect')

	return render_template('askdeleteuser.html',
		user_logged = user)

@app.route('/help', methods=['GET'])
def help():
	try:
		user = find_logged_user()
	except Exception as e:
		print(e)
	return render_template('help.html',
		user_logged = user)

@app.route('/addpost', methods=['GET', 'POST'])
@login_required
def addPost():
	url = 'editpost.html'
	user = getUserByEmail(login_session['email'])
	if user:
		# POST method add category
		if request.method == 'POST':
			# check if title and content exists
			title = request.form.get('title', None)
			content = request.form.get('post_content', None)
			picture = request.form['picture']
			if title and content:
				post = Post(title = title,
					user_id = user.id,
					picture = picture,
					post_content = content,
					date_added = datetime.datetime.now(),
					)
				session.add(post)
				session.commit()
				keywords = request.form['keywords'].split(',')
				try:
					for k in keywords:
						if k:
							k = Keyword(post_id = post.id,
								word = k)
							session.add(k)
							session.commit()
				except Exception as e:
					print e
					flash('Error in saving keywords')
				return redirect(url_for('showPost',
					post_id = post.id))
			else:
				# title or content is empty
				if request.form['origin'] == 'html':
					# html edit status
					url = 'editpost_html.html'
				flash('Title and Content must not be empty')
				return render_template(url,
					user_logged = user,
					post = None
					)

		# GET method shows add page
		if request.args.get('mode'):
			url = 'editpost_html.html'
		post = Post(title = '',
			post_content = '',
			picture = '')
		return render_template(url,
			post = post,
			edit = False,
			user_logged = user)
	else:
		return redirect(url_for('login'))

@app.route('/showpost/<int:post_id>', methods=['GET'])
def showPost(post_id):
	post = find_post(post_id)
	comments = find_comments(post_id)
	keywords = find_keywords(post_id)
	if post:
		return render_template('showpost.html',
			post = post,
			comments = comments,
			keywords = keywords,
			user_logged = find_logged_user())
	else:
		flash('Post not found')
		return render_template('error.html')

@app.route('/showpost_test/<int:post_id>', methods=['GET'])
@login_required
def showPostTest(post_id):
	# this post page render doesn't display comments
	# but displays a counter for answers marked as correct
	post = find_post(post_id)
	keywords = find_keywords(post_id)
	user_logged = find_logged_user()
	if post:
		return render_template('showpost_test.html',
			post = post,
			keywords = keywords,
			user_logged = user_logged)
	else:
		flash('Post not found')
		return render_template('error.html')

@app.route('/showpost_test/<int:post_id>/json', methods=['GET'])
@login_required
def showPostTestJson(post_id):
	user = find_logged_user()
	answers = find_test(post_id, user.id)
	if answers:
		return jsonify(Answers = [i.serialize for i in answers])
	else:
		err = { 
			'status': 404,
			'message': 'Error: Not Found'
		}
		resp = jsonify(err)
		resp.status_code = 404
		return resp

@app.route('/savetest/<int:post_id>/<int:user_id>', methods=['POST'])
@login_required
def saveTest(post_id, user_id):
	answers = request.form.getlist('test_results')
	if answers:
		for a in answers:
			print a
			test = Test(user_id = user_id,
				post_id = post_id,
				answer = a)
			session.add(test)
		session.commit()

		flash('Saved Test Results')
		return redirect(url_for('showPost', post_id = post_id))

@app.route('/updatetest/<int:post_id>/<int:user_id>', methods=['POST'])
@login_required
def updateTest(post_id, user_id):
	updated_answers = request.form.getlist('test_results')
	if updated_answers:
		for u in updated_answers:
			split_u = u.split('##')
			id = split_u[0]
			update = split_u[1]
			test = session.query(Test).filter_by(id = id).one()
			test.answer = update
			session.add(test)
		session.commit()
		flash('Answers updated in database')
	return redirect(url_for('showPostTest', post_id = post_id))

@app.route('/showpostcomment/<int:post_id>/<int:comment_id>', methods=['GET'])
@login_required
def showPostComment(post_id, comment_id):
	# this route renders a post page with comment editing in the
	# same field as the add comment form populated
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
				user_logged = user)
		else:
			flash('Not authorized')
			return render_template('error.html')
	else:		
		flash('Post not found')
		return render_template('error.html')	

@app.route('/editpost/<int:post_id>', methods=['GET', 'POST'])
@login_required
def editPost(post_id):
	url = 'editpost.html'
	user = find_logged_user()
	post = find_post(post_id)
	# check if logged in user is the author
	if user.id == post.user_id:

		# POST method edit 
		if request.method == 'POST':
			try:
				post.title = request.form['title']
				post.post_content = request.form['post_content']

				if post.title and post.post_content:
					post.date_added = datetime.datetime.now()
					session.add(post)
					session.commit()
			except Exception as e:
				print e
				flash('Title and Content cannot be empty')
				return redirect(url_for('editPost', post_id = post.id))

			# get all previous keywords, get new keywords, if keywords 

			new_keywords = request.form['keywords'].split(',')
			try:
				old_keywords = find_keywords(post.id)
				old_remaining_words = []
				for old_key in old_keywords:
					if not old_key.word in new_keywords:
						# delete words
						session.delete(old_key)
						session.commit()
					else:
						old_remaining_words.append(old_key.word)

				for k in new_keywords:
					# check if keyword is not an empty string
					# and does not exist already
					if k and (not k in old_remaining_words):
						keyword = Keyword(post_id = post.id,
									word = k)
						session.add(keyword)
						session.commit()
			except Exception as e:
				print e
				flash('Error saving keywords')
			return redirect(url_for('showPost', post_id = post_id))

		# GET method
		if request.args.get('mode'):
			url = 'editpost_html.html'
		return render_template(url,
			user_logged = user,
			edit = True,
			keywords = find_keywords(post.id) or None,
			post = post)

	else:
		flash('Not authorized to edit this post')
		return render_template('error.html')

@app.route('/showpostsbykey/<word>', methods=['GET'])
def showPostsByKey(word):
	return render_template('showpostsbykey.html',
		word = word,
		posts = find_posts_by_key(word),
		user_logged = find_logged_user())

@app.route('/query', methods=['GET', 'POST'])
def query():
	# query all titles and keywords
	word = request.form['word']
	print word
	if word:
		try:
			title_posts = session.query(Post).filter(or_(Post.title.like('%{}%'.format(word)),
																							Post.post_content.like('%{}%'.format(word)))).all()
			return render_template('showpostsquery.html',
				word = word,
				title_posts = title_posts,
				user_logged = find_logged_user())
		except Exception as e:
			print e
			flash('No posts found')
			return render_template('error.html',
				user_logged = find_logged_user())

@app.route('/askdelete/<int:post_id>', methods=['GET'])
def askDelete(post_id):
	mode = request.args.get('mode')
	return render_template('askdelete.html',
		user_logged = find_logged_user(),
		mode = mode or None,
		post_id = post_id)

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
				return redirect(url_for('showUser', user_id = user.id))
		else:
			flash('Not authorized to delete this post')
			return render_template('error.html')
	else:
		flash('Post not found')
		return render_template('error.html')

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
			flash('Not authorized to edit comment')
			return render_template('error.html')
	else:
		flash('Post / Comment not found')
		return render_template('error.html')

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
			flash('Not authorized to delete comment')
			return render_template('error.html')
	else:
		flash('Post / Comment not found')
		return render_template('error.html')


if __name__ == '__main__':
	app.debug = True
	app.secret_key = secret()
	app.run(host='0.0.0.0', port = 15000)