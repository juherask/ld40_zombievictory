
# A very simple Flask Hello World app for you to get started with...

from flask import Flask
from flask import flash, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config["DEBUG"] = True

# copypasta from A beginner's guide to building a simple database-backed Flask
# website on PythonAnywhere
# https://blog.pythonanywhere.com/121/
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="yorak",
    password="Y4go8CUX",
    hostname="yorak.mysql.pythonanywhere-services.com",
    databasename="yorak$ld40_zombievictory",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Unit(db.Model):
    __tablename__ = "units"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    owner_id = db.Column(db.Integer)
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    dx = db.Column(db.Integer)
    dy = db.Column(db.Integer)
    status = db.Column(db.String(32))
    intitiated = db.Column(db.DateTime)
    finishes = db.Column(db.DateTime)

class Leader(db.Model):
    __tablename__ = "leaders"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))
    insanity = db.Column(db.Integer)

class Shelter(db.Model):
    __tablename__ = "shelters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    owner_id = db.Column(db.Integer)
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    level = db.Column(db.Integer)
    
@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('map.html')
 
@app.route('/login', methods=['POST'])
def do_login():
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in'] = True
    else:
        flash('wrong password!')
    return home()

@app.route('/map', methods=['POST'])
def draw_map():
    sprite_id, sprite_x, sprite_y = (1,1,1)
    """
    div.sprite%d {
        position: fixed;
        bottom: %d;
        right: %d;
        width: 8px;
        height: 8px;
        border: 0px
    }"""%(sprite_id, sprite_x, sprite_y)
    
if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
    #app.run(debug=True)


