#Mindwelder Blog (Flask app)

## Synopsis

This project is a multi-user blog platform that can be used as a standard blog but also as a 'quick set-up' learning application.

Highlight sections of your post and style it with an underline using the included Rich Text Editor (or add a u html tag in it, in HTML editor mode) and it will automatically be parsed as a test answer. When you read it in 'TEST MODE', that section can now be used as a fill-in-the blank answer. There is a counter that states the number of answers you've marked as correct and a total of the answers.

You can grab any post in the app or paste one you find anywhere, and test yourself with it. Furthermore every test can be saved on the database, so that when you go back to it, you can pick up where you left at. Essentially you are testing yourself manually and marking every answer correct or incorrect (which will toggle between hiding or showing the answer).

The app is live at https://www.mindwelder.com (hosted on a Digital Ocean VPS with Ubuntu 14.04 with the Cloudflare CDN).

## Motivation

Have you ever wanted to grab a post and quickly try to memorize it or quiz yourself on it? You can do that with this application. Paste or write anything then 'underline' it to make it an answer. Every answer when viewed on 'test mode' will show up hidden but marked with an underline, when you click on it, that section will be displayed and marked as a correct answer. Click it again to hide it if you want to test yourself again. It's that simple. All your progress is saved too and you can pick up where you left off afterwards.

## Mind map of Mindwelder.com
![Mind map](https://cloud.githubusercontent.com/assets/15892944/21464469/e5b3cf9e-c932-11e6-8447-a3841fe6d88b.png)


* NOTE : The green nodes indicate Publicly viewed pages, the gray nodes indicate Private (User-logged in) pages.

## Code Features
1. jQuery
2. jQuery
3. PostgreSQL database
4. SQLAlchemy ORM
5. jQuery for AJAX calls
6. Code Prettify by https://github.com/google/code-prettify

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
