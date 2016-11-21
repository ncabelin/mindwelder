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

CLIENT_ID = json.loads(
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

@app.route('/login')
def login():
	return render_template('login.html')


if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port = 15000)