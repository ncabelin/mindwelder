#Mindwelder Blog (Flask app)

## Synopsis

This project is a multi-user blog platform that can be used as a standard blog but also as a 'quick set-up' learning application.

Highlight sections of your post, underline it with the included Rich Text Editor or add a u html tag in it and it will automatically be parsed as a test answer. When you read it on 'test mode', that section can now be used as a fill-in-the blank answer. There is a section that states the number of answers you've marked as correct and a total of the answers.

Grab any post and test yourself with it. Furthermore every test can be saved on the database, so that when you go back to it, you can pick up where you left at. Essentially you are testing yourself manually and marking every answer correct or incorrect (which will toggle between hiding or showing the answer).

The app is live at https://www.mindwelder.com

## Motivation

Have you ever wanted to grab a post and quickly try to memorize it or quiz yourself on it? You can do that with this application. Paste or write anything then 'underline' it to make it an answer. Every answer when viewed on 'test mode' will show up hidden but marked with an underline, when you click on it, that section will be displayed, and marked as a correct answer. Click it again to hide it, if you want to test yourself again. It's that simple. You can save your progress too and pick up where you left off afterwards.

## Code Features
1. Oauth2.0 Auth and Authorization with Google+, Facebook along with own User registration
2. Flask library
3. PostgreSQL database
4. SQLAlchemy ORM
5. jQuery AJAX

## Installation
1. Install dependencies :
	* flask
	* oauth2client
	* requests
	* sqlalchemy
	* bleach
	* bcrypt
	* flask_mail
	* itsdangerous

2. Create your own secretkeys.py file and write in your secret key :
```
def secret():
	return 'Paste_your_secret_key_here'
```

3. Create and register your own json files for 'client_secret_mw.json' for Google+, and 'fbclient_secret.json' :

### Facebook
```
{
	"web": {
		"app_id": "PASTE_APP_ID_HERE_FROM_FB_APP_REGISTRATION_PAGE",
		"app_secret": "PASTE_APP_SECRET_HERE_FROM_FB_APP_REGISTRATION_PAGE"
	}
}
```

### Google+ registration, (can be downloaded)
download the json file from the registration page

## Future feature implementation
1. Add 'captcha'
2. CRON job? check if user has confirmed within specific amount of time

## Contributors

Neptune Michael Cabelin

## License

MIT
