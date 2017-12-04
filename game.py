
from flask import Flask
from flask import flash, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
import os, hashlib, uuid
from random import random, choice

app = Flask(__name__)
app.config['DEBUG'] = True

# use sqlite for debugging
#todo: remove later, check running on the dev machine
if os.name == 'nt':
    SQLALCHEMY_DATABASE_URI = 'sqlite:///C:\\MyTemp\\ld40_zombievictory.db'
else:
	# copypasta from A beginner's guide to building a simple database-backed Flask
	# website on PythonAnywhere
	# https://blog.pythonanywhere.com/121/
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}'.format(username='yorak', password='Y4go8CUX', hostname='yorak.mysql.pythonanywhere-services.com', databasename='yorak$ld40_zombievictory')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_POOL_RECYCLE'] = 299
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Visibility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer)
    shelter_id = db.Column(db.Integer)
    owner_id = db.Column(db.Integer)
    visible_to_id = db.Column(db.Integer)


class Unit(db.Model):
    __tablename__ = 'units'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    owner_id = db.Column(db.Integer)
    shelter_id = db.Column(db.Integer)
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    dx = db.Column(db.Integer)
    dy = db.Column(db.Integer)
    status = db.Column(db.String(32), default='quarantine')
    intitiated = db.Column(db.DateTime)
    finishes = db.Column(db.DateTime)
    is_leader = db.Column(db.Boolean, default=False)
    is_zombie = db.Column(db.Boolean, default=False)
    is_infected = db.Column(db.Boolean, default=False)
    when_infected = db.Column(db.DateTime)


class Leader(db.Model):
    __tablename__ = 'leaders'
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer)
    name = db.Column(db.String(128))
    salt = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))
    insanity = db.Column(db.Integer, default=0)
    is_dead = db.Column(db.Boolean, default=False)


class Shelter(db.Model):
    __tablename__ = 'shelters'
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
    __tablename__ = 'casualities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    owner_id = db.Column(db.Integer)
    killed_by = db.Column(db.String(512))


MAP_WIDTH = 600
MAP_HEIGHT = 600
MIN_BASE_DIST = 20
RANDOM_BASE_PLACEMENT_RETRIES = 10
INITIAL_RESOURCES = 10
INITIAL_SURVIVORS = 3
FORENAMES = [
 'Matti', 'Timo', 'Juha', 'Kari', 'Antti', 'Mikko', 'Jari', 'Pekka',
 'Jukka', 'Markku', 'Mika', 'Hannu', 'Heikki', 'Tuula', 'Seppo', 'Ritva',
 'Leena', 'Anne', 'P\xc3\xa4ivi', 'Pirjo']
SURNAMES = [
 'Korhonen', 'Virtanen', 'M\xc3\xa4kinen', 'Nieminen', 'M\xc3\xa4kel\xc3\xa4', 'H\xc3\xa4rn\xc3\xa4lainen',
 'Laine', 'Heikkinen', 'Koskinen', 'J\xc3\xa4rvinen', 'Lehtonen', 'Lehtinen',
 'Saarinen', 'Salminen', 'Heinonen', 'Heikkil\xc3\xa4', 'Niemi', 'Salonen',
 'Kinnunen', 'Turunen']

def create_new_base_shelter(userid, username):
    retries = RANDOM_BASE_PLACEMENT_RETRIES
    while True:
        if retries == 0:
            return None
        base_x = int(random() * MAP_WIDTH)
        base_y = int(random() * MAP_HEIGHT)
        shelter_too_close = Shelter.query.filter(Shelter.x > base_x - MIN_BASE_DIST, Shelter.x < base_x + MIN_BASE_DIST, Shelter.y > base_y - MIN_BASE_DIST, Shelter.y < base_y - MIN_BASE_DIST).first()
        if not shelter_too_close:
            break

    new_base = Shelter(name=username + "'s shelter", owner_id=userid, x=base_x, y=base_y, resource_food=INITIAL_RESOURCES, resource_meds=INITIAL_RESOURCES, resource_guns=INITIAL_RESOURCES)
    db.session.add(new_base)
    db.session.commit()
    for i in range(INITIAL_SURVIVORS - 1):
        new_survivor = Unit(name=choice(FORENAMES) + ' ' + choice(SURNAMES), owner_id=userid, shelter_id=new_base.id, x=base_x, y=base_y, dx=0, dy=0, status='sheltered')
        db.session.add(new_survivor)
        db.session.commit()

    leader_survivor = Unit(name=username, owner_id=userid, shelter_id=new_base.id, x=base_x, y=base_y, dx=0, dy=0, status='sheltered', is_leader=True)
    db.session.add(leader_survivor)
    db.session.commit()
    return new_base


@app.route('/')
def home():
    shelter_cnt = Shelter.query.count()
    survivor_cnt = Unit.query.filter_by(is_zombie=False).count()
    leader_cnt = Leader.query.count()
    casuality_cnt = Casuality.query.count()
    return render_template('cover.html', shelter_cnt=shelter_cnt, survivor_cnt=survivor_cnt, leader_cnt=leader_cnt, casuality_cnt=casuality_cnt)


@app.route('/', methods=['POST'])
def home_action():
    if request.method == 'POST':
        if request.form['submit'] == 'Play' and session['logged_in']:
            return redirect('/map', code=302)
        if request.form['submit'] == 'Register':
            return render_template('register.html')
        if request.form['submit'] == 'Log in':
            return render_template('login.html')
    flash('invalid post!')
    return redirect('/', code=302)


@app.route('/login', methods=['POST'])
def do_login():
    user = Leader.query.filter_by(name=request.form['username']).first()
    if user:
        hashed_password = hashlib.sha512(request.form['password'] + user.salt).hexdigest()
        target_pw_hash = user.password_hash
        if hashed_password == target_pw_hash:
            session['logged_in'] = True
            session['used_id'] = user.id
            return home()
    flash('wrong name or password!')
    return home()


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect('/')


@app.route('/register', methods=['POST'])
def new_user():
    existing_user = Leader.query.filter_by(name=request.form['username']).first()
    if existing_user:
        flash('username already taken!')
        return home()
    else:
        salt = uuid.uuid4().hex
        hashed_password = hashlib.sha512(request.form['password'] + salt).hexdigest()
        hashed_retypepw = hashlib.sha512(request.form['retypepw'] + salt).hexdigest()
        if hashed_password == hashed_retypepw:
            new_leader = Leader(name=request.form['username'], salt=salt, password_hash=hashed_password, insanity=0)
            db.session.add(new_leader)
            db.session.commit()
            base = create_new_base_shelter(new_leader.id, new_leader.name)
            if base == None:
                db.session.delete(new_leader)
                db.session.commit()
                flash('server is full, try again later!')
                return home()
            session['logged_in'] = True
            session['used_id'] = new_leader.id
            return home()
        flash('passwords do not match!')
        return home()
        return


@app.route('/map')
def map_view():
    user_units = Unit.query.filter_by(owner_id=session['used_id']).all()
    user_shelters = Shelter.query.filter_by(owner_id=session['used_id']).all()
    return render_template('map.html', user_units=user_units, user_shelters=user_shelters, visible_units=user_units, visible_shelters=user_shelters)


@app.route('/map', methods=['POST'])
def map_action():
    sprite_id, sprite_x, sprite_y = (1, 1, 1)
    '\n    div.sprite%d {\n        position: fixed;\n        bottom: %d;\n        right: %d;\n        width: 8px;\n        height: 8px;\n        border: 0px\n    }' % (sprite_id, sprite_x, sprite_y)


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
	#todo: remove later, check running on the dev machine
    if os.name == 'nt':
        app.run(debug=True, host='0.0.0.0', port=4000)
    else:
        app.run(debug=True)
