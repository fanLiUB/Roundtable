import flask
from flask import Flask, Response, request, render_template, redirect, url_for, send_from_directory, session
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
from flask_oauth import OAuth
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map
import json
import os

from flask import Flask
app = Flask(__name__)

app.config.update(
    DEBUG = True,
)
#database setup
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '112358'
app.config['MYSQL_DATABASE_DB'] = 'roundtable'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#login_code
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email from Users")
    return cursor.fetchall()

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not(email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not(email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0] )
    user.is_authenticated = request.form['password'] == pwd
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return render_template('homepage.html')
    #The request method is POST (page is recieving data)
    email = flask.request.form['email']
    cursor = conn.cursor()
    #check if email is registered
    if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0] )
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user) #okay login in user
            uid = getUserIdFromEmail(flask_login.current_user.id)
            return flask.redirect(flask.url_for("facebook_login"))
    #information did not match
    return "<a href='/login'>Try again</a>\
            </br><a href='/register'>or make an account</a>"


@app.route('/profile')
@flask_login.login_required
def protected():
    return render_template('404.html')

@app.route('/logout')
def logout():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Map WHERE user_id ='{0}'".format(uid))
    conn.commit()
    flask_login.logout_user()
    return render_template('homepage.html')

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
    return render_template('register.html', supress='True')

@flask_login.login_required
@app.route("/register_course", methods=['GET', 'POST'])
def register_course():
    if flask.request.method == 'GET':
        return render_template('register_course.html')
    else:
        uid = getUserIdFromEmail(flask_login.current_user.id)
        course_title = request.form.get('course_title')
        course_number = request.form.get('course_number')
        if checkUniqueClass(course_number):
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Courses (course_title, course_number) VALUES ('{0}', '{1}')".format(course_title, course_number))
            conn.commit()
        # add info to User_Has_Courses table
        if checkUniqueUser_in_Class(uid):
            secondcursor = conn.cursor()
            secondcursor.execute("SELECT course_id FROM Courses WHERE course_number = '{0}'".format(course_number))
            course_id = secondcursor.fetchone()[0]
            print course_id
            newcursor = conn.cursor()
            newcursor.execute("INSERT INTO User_Has_Courses(course_id, user_id) VALUES('{0}','{1}')".format(course_id, uid))
            conn.commit()
        return flask.redirect(flask.url_for("facebook_login"))
        #return render_template("map_test3.html", user_picture_url = get_facebook_profile_url(), user_info = getUserInfoFromId(uid))
        #return render_template('home_page_template.html', user_name = getUserNameFromId(uid))

def checkUniqueClass(course_number):
    secondcursor = conn.cursor()
    if secondcursor.execute("SELECT course_id FROM Courses WHERE course_number = '{0}'".format(course_number)):
        return False
    else:
        return True

def checkUniqueUser_in_Class(uid):
    secondcursor = conn.cursor()
    if secondcursor.execute("SELECT user_id FROM User_Has_Courses WHERE user_id = '{0}'".format(uid)):
        return False
    else:
        return True

@app.route("/register", methods=['POST'])
def register_user():
    u_fname=request.form.get('u_fname')
    u_lname=request.form.get('u_lname')
    email=request.form.get('email')
    password=request.form.get('password')
    year_of_grad=request.form.get('year_of_grad')
    education=request.form.get('education')
    cursor = conn.cursor()
    test =  isEmailUnique(email)
    if test:
        print cursor.execute("INSERT INTO Users (email, password, u_fname, u_lname, year_of_grad, university) VALUES ('{0}', '{1}','{2}','{3}','{4}','{5}')".format(email, password, u_fname, u_lname, year_of_grad, education))
        conn.commit()
        #log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return flask.redirect(flask.url_for('register_course'))
    else:
        print "couldn't find all tokens"
        return flask.redirect(flask.url_for('register'))

def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
    return cursor.fetchone()[0]

def getUserNameFromId(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT u_fname, u_lname FROM Users WHERE user_id = '{0}'".format(uid))
    return cursor.fetchone()

def getUserInfoFromId(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT u_fname, u_lname, university, year_of_grad FROM Users WHERE user_id = '{0}'".format(uid))
    return cursor.fetchone()

def isEmailUnique(email):
    #use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
        #this means there are greater than zero entries with that email
        return False
    else:
        return True
#end of login code


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'ico/favicon.ico')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

app.secret_key = 'super secret string'  # Change this!
app.config['GOOGLEMAPS_KEY'] = 'AIzaSyDPIxQ95g3W-PAd0WPy_PjM84-HtAKQp1U'
FACEBOOK_APP_ID = '1672494819728765'
FACEBOOK_APP_SECRET = 'f7e34d53d0c62215f2b8a92f59941a89'


oauth = OAuth()
facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret= FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email'}
)

@facebook.tokengetter
def get_facebook_token():
    return session.get('facebook_token')

def pop_login_session():
    session.pop('logged_in', None)
    session.pop('facebook_token', None)

@app.route("/facebook_login")
def facebook_login():
    return facebook.authorize(callback=url_for('facebook_authorized',next=request.args.get('next'), _external=True))

@app.route("/facebook_authorized")
@facebook.authorized_handler
def facebook_authorized(resp):
    next_url = request.args.get('next') or url_for('mapview')
    if resp is None or 'access_token' not in resp:
        return redirect(next_url)
    session['logged_in'] = True
    session['facebook_token'] = (resp['access_token'], '')
    uid = getUserIdFromEmail(flask_login.current_user.id)
    #return render_template("map_test3.html", user_picture_url = get_facebook_profile_url(), user_info = getUserInfoFromId(uid))
    return flask.redirect(flask.url_for('mapview'))
    #return flaskredirect(next_url,user_picture_url = get_facebook_profile_url(), user_info = getUserInfoFromId(uid))

@app.route("/logout_facebooklogin")
def logout_facebook():
    pop_login_session()
    return render_template('home_page_template.html', message="Logged out")

#Querying information from facebook
def get_facebook_name():
	data = facebook.get('/me').data
	print data
	if 'id' in data and 'name' in data:
		user_id = data['id']
		user_name = data['name']
		return user_name

def get_facebook_friend_appuser():
	data = facebook.get('/me?fields=friends{first_name,last_name}').data
	print data
	return data


def get_all_facebook_friends():
	data = facebook.get('/me/taggable_friends?fields=first_name,last_name').data
	print data
	return data

def get_facebook_profile_url():
    data = facebook.get('/me?fields=picture{url}').data
    if 'picture' in data:
        print data['picture']
        json_str = json.dumps(data['picture'])
        resp = json.loads(json_str)
        print "json object"
        user_picture_url = data['picture']
        return data['picture']['data']['url']






#This is for profile editing
@app.route("/Profile/<user_id>/edit", methods = ['GET','POST'])
def edit_profile(user_id):
	if request.method == 'POST':
		return render_template('profile_edit.html')
	else:
		return render_template('profile_edit.html')


@flask_login.login_required
@app.route("/addMarker", methods = ['GET', 'POST'])
def addMarker():
    if flask.request.method == 'GET':
        return flask.redirect(flask.url_for('mapview'))
    else:
        uid = getUserIdFromEmail(flask_login.current_user.id)
        lat = request.form.get('latitude')
        lng = request.form.get('longitude')
        message = request.form.get('message')
        contact_method = request.form.get('contact_method')
        course_info = request.form.get('course_title')
        resultString = course_info +" " + message + " " + contact_method
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Messages(user_id, content) VALUES ('{0}','{1}')".format(uid,resultString))
        conn.commit()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Map(latitude, longitude, message, user_id) VALUES ('{0}','{1}','{2}','{3}')".format(lat,lng,resultString,uid))
        conn.commit()
        return flask.redirect(flask.url_for('mapview'))





GoogleMaps(app)
#google map testing
@app.route("/mapview")
@flask_login.login_required
def mapview():
    # creating a map in the view
    mymap = Map(
        identifier="view-side",
        lat=37.4419,
        lng=-122.1419,
        markers=[(37.4419, -122.1419)]
    )
    sndmap = Map(
        identifier="sndmap",
        lat=37.4419,
        lng=-122.1419,
        markers=[
          {
             'icon': 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
             'lat': 37.4419,
             'lng': -122.1419,
             'infobox': "<b>Come and find me</b>"
          },
          {
             'icon': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
             'lat': 37.4300,
             'lng': -122.1400,
             'infobox': "<b>Hey, I am here!!!</b>"
          }
        ]
    )
    resultArray = []
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT latitude, longitude, message FROM Map")
    markers = cursor.fetchall()
    for x in markers:
        resultArray.append(x)
    print resultArray
    return render_template('map_test3.html', user_info = getUserInfoFromId(uid), user_picture_url = get_facebook_profile_url(), mymap=mymap, sndmap=sndmap, Marker = markers)

@app.route("/map_unsafe")
def map_unsafe():
    return render_template('map_test3.html')

@app.route("/")
def index():
	#name = get_facebook_name()
	#friends = get_facebook_friend_appuser()
	#all_friends = get_all_facebook_friends()
	#return render_template('home_page_template.html', message = 'Welcome to RoundTable', user_name = get_facebook_name(), user_picture_url = get_facebook_profile_url())
    return render_template('homepage.html', message = 'Welcome to RoundTable')

#homepage
@app.route("/welcome")
def welcome():
    return render_template('homepage.html', message = "Welcome to RoundTable. You can get your profile pic through facebook")


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
