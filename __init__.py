# TO DO:
# add forgot password, use gmail to send activate
# add flask recaptcha during registration
# add post setting to private, public
# add list of tests taken in profile settings
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
from flask_mail import Message, Mail

from flask import session as login_session
from flask import make_response
from itsdangerous import URLSafeSerializer
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
from functools import wraps
import bleach
from bcrypt import hashpw, checkpw, gensalt
from secretkeys import secret

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = secret('username')
app.config['MAIL_PASSWORD'] = secret('password')
mail = Mail(app)

from sqlalchemy import create_engine, desc, or_
from sqlalchemy.orm import sessionmaker
from database import Base, User, Post, Like, Comment, Keyword, Test

engine = create_engine('postgresql://meeska:Marcopupu2014@localhost:5432/mindwelder')
DBSession = sessionmaker(bind = engine)
session = DBSession()

# internal modules
from validators import valid_username, valid_email, valid_password
from parser import markdown

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
	except Exception as e:
		print(e)
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
	user = getUserByEmail(login_session['email'])
	if not user:
		try:
			newUser = User(username = login_session['username'],
				email = login_session['email'],
				account = account,
				confirmed = True,
				registered_on = datetime.datetime.now(),
				picture = login_session['picture'])
			session.add(newUser)
			session.commit()
			user = session.query(User).filter_by(email = login_session['email']).one()
			return user.id
		except Exception as e:
			print(e)
			flash(e)
			return None;
	else:
		return None

# token registration
def generate_confirmation_token(email, secret_key):
	serializer = URLSafeSerializer(secret_key)
	return serializer.dumps(email)

def confirm_token(token, secret_key):
	serializer = URLSafeSerializer(secret_key)
	try:
		email = serializer.loads(token)
	except:
		return False
	return email

def send_confirmation_token(token, recipient):
	msg = Message(
		'Welcome to Mindwelder Blogs',
		sender = secret('email'),
		recipients = [recipient]
	)
	msg.html = """Welcome to <b>Mindwelder Blogs</b>,
		Thanks for signing up, Please
		follow this link to activate your account :
		 <a href='https://www.mindwelder.com/confirm/{}'>
		 https://www.mindwelder.com/confirm/{}</a>
		""".format(token, token)
	mail.send(msg)
	return 'sent'

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
		post_ids = session.query(Keyword.post_id).filter_by(
			word = word).group_by(Keyword.post_id).all()
		posts = []
		for p in post_ids:
			post = session.query(Post).filter_by(
				id = p.post_id).one()
			posts.append(post)
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

def create_alert(msg, alert):
	return ('<div class="alert alert-{}">{}<a href="" class="close" ' +
	'data-dismiss="alert">&times;</a></div>').format(alert, msg)

# decorator function
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
	if (link[:19] == 'http://i.imgur.com/') and (len(link) < 100):
		newLink = 'https://i.imgur.com/' + link[19:]
		return newLink
	elif (link[:20] == 'https://i.imgur.com/') and (len(link) < 100):
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
		print 'wtf'

		# check if 2 passwords match
		if password != verify:
			flash(create_alert("Password's don't match", "danger"))
			return redirect('/register')

		# check if password is not blank or below 8 characters
		password = valid_password(password)

		if not username:
			flash(create_alert("Username is not valid", "danger"))
		if not password:
			flash(create_alert("Password is not valid", "danger"))
		if not email:
			flash(create_alert("Email is not valid", "danger"))

		if getUserByEmail(email):
			flash(create_alert("Another user has registered with that email, please use another one", "danger"))
			return redirect('/register')

		if username and valid_email(email) and password:
			newUser = User(
				username = username,
				description = request.form['description'],
				confirmed = False,
				registered_on = datetime.datetime.now(),
				email = email,
				password = hashpw(password.encode('utf-8'), gensalt()),
				picture = '/static/images/generic.png',
				account = 'mindwelder'
				)

			try:
				session.add(newUser)
				session.commit()
				token = generate_confirmation_token(email, secret('key'))
				send_confirmation_token(token, email)
				flash(create_alert('Please go to your email account' +
				' to confirm', 'success'))
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

@app.route('/confirm/<token>', methods = ['GET'])
def confirm(token):
	email = confirm_token(token, secret('key'))
	if email:
		user = getUserByEmail(email)
		if user:
			user.confirmed = True
			session.add(user)
			session.commit()
			flash(create_alert('Confirmation successful, Please log in','success'))
			return redirect('/login')
	flash('Error confirming')
	return render_template('error.html')

@app.route('/unconfirmed', methods = ['GET'])
@login_required
def unconfirmed():
	return render_template('unconfirmed.html')

@app.route('/forgotpassword/<token>', methods = ['GET', 'POST'])
def forgotPassword(token):
	secret_key = 'reset' + secret('key')
	if request.method == 'POST':
		# send email with link to reset password
		email = request.form['email']
		user = getUserByEmail(email)
		print(email, user)
		if user:
			msg = Message('Reset Password Request',
				sender = secret('email'),
				recipients = [email])
			g_token = generate_confirmation_token(email, secret_key)
			msg.html = """
			<h1>Mindwelder</h1>
			<p>A Password reset request has been sent. Follow this link
			to enter a new password.</p>
			<a href='localhost:15000/forgotpassword/{}'>localhost:15000/forgotpassword/{}</a>
			""".format(g_token, g_token)
			mail.send(msg)
			return render_template('forgotpassword_link_sent.html', email = email)
		else:
			flash('That email does not exist in our system')
			return render_template('error.html')
	if token == '0':
		return render_template('forgot.html')
	return render_template('reset.html', token = token)

@app.route('/resetpassword', methods = ['POST'])
def resetPassword():
	if request.method == 'POST':
		secret_key = 'reset' + secret('key')
		token = request.form['token']
		email = confirm_token(token, secret_key)
		password = valid_password(request.form['password'])
		verify = request.form['verify']
		if email and password and (password == verify):
			try:
				user = getUserByEmail(email)
				user.password = hashpw(password.encode('utf-8'), gensalt())
				session.add(user)
				session.commit()
				flash(create_alert('Password changed, please log in with your new password','success'))
				return redirect('/login')
			except Exception as e:
				print(e)
				flash(e)
				return render_template('error.html')
		flash('Invalid Token')
		return render_template('error.html')


@app.route('/mconnect', methods = ['POST'])
def mconnect():
	email = request.form['email']
	password = request.form['password']
	try:
		user = session.query(User).filter_by(email = email).one()
		hashed = user.password.encode('utf-8')
		if (hashpw(password.encode('utf-8'),
			hashed) == hashed) and (user.confirmed == True):
			login_session['user_id'] = user.id
			login_session['description'] = user.description or None
			login_session['provider'] = user.account
			login_session['username'] = user.username
			login_session['picture'] = user.picture
			login_session['email'] = user.email
			flash(create_alert('User logged in as {}'.format(user.username),'success'))
			return redirect('/')
		else:
			flash(create_alert('Username / Password not valid or' +
			 ' User has not confirmed his email','danger'))
			return redirect(url_for('login'))
	except:
		flash(create_alert('Username / Password not valid','danger'))
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
	user = getUserByEmail(login_session['email'])
	if not user:
		user_id = createUser(login_session, 'google')
	elif user.account != 'google':
		return respond('Email already exists', 401)
	user_id = user.id
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
		if not user_id:
			return respond("Email already exists", 401)
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
			flash(create_alert('Logged out using Google+','success'))
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
		flash(create_alert('Logged out using Facebook','success'))
		return redirect(url_for('login'))

	elif login_session['provider'] == 'mindwelder':
		session_list = [
			'provider',
			'username',
			'email',
			'picture']
		for s in session_list:
			del login_session[s]
		flash(create_alert('Logged out','success'))
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
		flash(e)
		return render_template('error.html')
	if request.method == 'POST':
		user.username = request.form['username']
		user.description = request.form['description']
		user.picture = request.form['picture'] or '/static/images/generic.png'
		session.add(user)
		session.commit()
		flash(create_alert('Successfully edited user settings','success'))
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
		flash(e)
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
			description = request.form['description']
			if title and content:
				post = Post(title = title,
					user_id = user.id,
					picture = picture,
					description = description,
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
					flash(create_alert('Error in saving keywords','danger'))
				return redirect(url_for('showPost',
					post_id = post.id))
			else:
				# title or content is empty
				if request.form['origin'] == 'html':
					# html edit status
					url = 'editpost_html.html'
				flash(create_alert('Title and Content must not be empty','danger'))
				return render_template(url,
					user_logged = user,
					post = None
					)

		# GET method shows add page
		if request.args.get('mode'):
			url = 'editpost_html.html'
		post = Post(title = '',
			description = '',
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
	user = find_logged_user()
	answers = request.get_json();
	if answers:
		for a in answers:
			print a
			db_id = a.split('##')[0]
			if db_id == '0':
				# new answer, create new and retrieve id by flushing first
				# then modify answer to include id
				test = Test(user_id = user.id,
					post_id = post_id,
					answer = a)
				session.add(test)
				session.flush()
				before_answer = test.answer.split('##')
				before_answer[0] = str(test.id)
				after_answer = '##'.join(before_answer)
				test.answer = after_answer
			else:
				try:
					test = session.query(Test).filter_by(id = int(db_id)).one()
					test.answer = a
					session.add(test)
				except Exception as e:
					return respond('Error on database', 400)
		session.commit()
		return respond('Saved Test Results', 200)

@app.route('/updatetest/<int:post_id>/<int:user_id>', methods=['POST'])
@login_required
def updateTest(post_id, user_id):
	updated_answers = request.get_json()
	user = find_logged_user()
	if user.id == user_id:
		if updated_answers:
			for u in updated_answers:
				split_u = u.split('##')
				db_id = split_u[0]
				try:
					test = session.query(Test).filter_by(id = db_id).one()
					test.answer = u
					session.add(test)
				except Exception as e:
					return respond('Error accessing test', 400)
			session.commit()
		return respond('Test Results Updated', 200)
	else:
		return respond('Not authorized to update progress', 400)

@app.route('/deletetest/<int:post_id>/<int:user_id>', methods=['POST'])
@login_required
def deleteTest(post_id, user_id):
	progress_owner = request.get_json()
	logged_user = find_logged_user()
	# check ownership of test
	if user_id == logged_user.id:
		try:
			test = session.query(Test).filter_by(post_id = post_id).filter_by(user_id = user_id).all()
			for t in test:
				session.delete(t)
			session.commit()
			return respond('Deleted all previous progress', 200)
		except Exception as e:
			print(e)
			return respond('something went wrong', 400);
	else:
		return respond('Not authorized to delete progress', 400)

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
				post.description = request.form['description']
				post.post_content = request.form['post_content']
				post.picture = request.form['picture']
				if post.title and post.post_content:
					post.date_added = datetime.datetime.now()
					session.add(post)
					session.commit()
			except Exception as e:
				print e
				flash(create_alert('Title and Content cannot be empty','danger'))
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
				flash(create_alert('Error saving keywords','danger'))
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
		flash(create_alert('Cannot like a post more than once','danger'))
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
	app.secret_key = secret('key')
	app.run(host='0.0.0.0', port = 15000)
