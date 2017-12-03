
# A very simple Flask Hello World app for you to get started with...

from flask import Flask
from flask import flash, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
import os
import hashlib, uuid

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

class Visibility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer)
    shelter_id = db.Column(db.Integer)
    owner_id = db.Column(db.Integer)
    visible_to_id = db.Column(db.Integer)
    
class Unit(db.Model):
    __tablename__ = "units"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    owner_id = db.Column(db.Integer)
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    dx = db.Column(db.Integer)
    dy = db.Column(db.Integer)
    status = db.Column(db.String(32), default="quarantine")
    intitiated = db.Column(db.DateTime)
    finishes = db.Column(db.DateTime)
    is_leader = db.Column(db.Boolean, default=False)
    is_zombie = db.Column(db.Boolean, default=False)

class Leader(db.Model):
    __tablename__ = "leaders"
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer)
    name = db.Column(db.String(128))
    salt = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))
    insanity = db.Column(db.Integer, default=0)
    is_dead = db.Column(db.Boolean, default=False)

class Shelter(db.Model):
    __tablename__ = "shelters"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    owner_id = db.Column(db.Integer)
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    level = db.Column(db.Integer, default=1)
    is_abandoned = db.Column(db.Boolean, default=False)
    resource_food = db.Column(db.Integer)
    resource_meds = db.Column(db.Integer)
    resource_guns = db.Column(db.Integer)
        
class Casuality(db.Model):
    __tablename__ = "casualities"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    owner_id = db.Column(db.Integer)
    killed_by = db.Column(db.String(512))
    
@app.route('/')
def home():
    shelter_cnt = Shelter.query.count()
    survivor_cnt = Unit.query.filter_by(is_zombie=False).count()
    leader_cnt = Leader.query.count()
    casuality_cnt = Casuality.query.count()
    
    return render_template('cover.html',
               shelter_cnt = shelter_cnt,
               survivor_cnt = survivor_cnt,
               leader_cnt = leader_cnt,
               casuality_cnt = casuality_cnt)

@app.route('/', methods=['POST'])
def from_home():
    if request.method == 'POST':
        if request.form['submit'] == 'Play' and session['logged_in']:
            user_units = Unit.query.filter_by(owner_id=request.form['used_id'])
            user_shelters = Shelter.query.filter_by(owner_id=request.form['used_id'])
            return render_template('map.html', 
                user_units = user_units, user_shelters = user_shelters,
                visible_units = user_units, visible_shelters = user_shelters)
        elif request.form['submit'] == 'Register':
            return render_template('register.html')
        elif request.form['submit'] == 'Log in':
            return render_template('login.html')
    
    flash('invalid post!')
    return redirect("/", code=302)
 
@app.route('/login', methods=['POST'])
def do_login():
    user = Leader.query.filter_by(username=request.form['username']).first()
    hashed_password = hashlib.sha512(request.form['password'] + user.salt).hexdigest()
    target_pw_hash = user.password_hash
    if hashed_password == target_pw_hash:
        session['logged_in'] = True
        session['used_id'] = user.id
    else:
        flash('wrong password!')
    return home()

@app.route('/register', methods=['POST'])
def new_user():
    salt = uuid.uuid4().hex
    hashed_password = hashlib.sha512(request.form['password'] + salt).hexdigest()
    hashed_retypepw = hashlib.sha512(request.form['retypepw'] + salt).hexdigest()
    
    if hashed_password == hashed_retypepw:
        new_leader = Leader(
            name=request.form['username'],
            salt=salt,
            password_hash=hashed_password,
            insanity=0
        )
        db.session.add(new_leader)
        db.session.commit()
        
        session['logged_in'] = True
        #todo: check that this gets set
        session['used_id'] = new_leader.id
        return home()
    else:
        flash('passwords do not match!')
        return new_user()

@app.route('/map', methods=['POST'])
def map_action():
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

    #todo: remove later, check running on the dev machine
    if os.name == 'nt':
        app.run(debug=True,host='0.0.0.0', port=4000)
    else:
        app.run(debug=True)


