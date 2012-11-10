import os
from datetime import datetime
from flask import Flask, jsonify, request
from flask_heroku import Heroku
from flask.ext.sqlalchemy import SQLAlchemy

# for password hashing
from werkzeug.security import generate_password_hash, check_password_hash

app       = Flask (__name__)
app.debug = True

heroku    = Heroku (app)
db        = SQLAlchemy (app)

class API_Response:
  def __init__(self, status="ERR", objs=[], error=""):
   self.status = status
   self.error  = error
   self.objs   = objs

  def as_dict(self):
    return {"meta"    : {"status":self.status,"error":self.error},
            "objects" : self.objs}

# CONTROLLERS

@app.route("/")
def index():
  return "Hello Latitune!"

# USERS

@app.route("/api/user", methods=['PUT'])
def create_user():
  try:
    if all ([arg in request.form for arg in ['username','email','password']]):
      new_user = User(request.form['username'],
                      request.form['email'],
                      request.form['password'])
      db.session.add(new_user)
      db.session.commit()
      return jsonify(API_Response("OK", [new_user.serialize]).as_dict())
    else:
      raise Exception
  except Exception as e:
    return jsonify(API_Response("ERR", [], str(e)).as_dict())

# BLIPS

@app.route("/api/blip", methods=['GET'])
def get_blip():
  if all([arg in request.args for arg in ['latitude','longitude']]):
    lat = request.args['latitude']
    lng = request.args['longitude']
    db.commit()    
    query = "SELECT id, " \
      "( 3959 * acos( cos( radians(37) ) * cos( radians( %(lat)i ) ) * " \
      "cos( radians( %(lng)i ) - radians(-122) ) + sin( radians(37) ) * " \
      "sin( radians( %(lat)i ) ) ) ) AS distance from blip " \
      "order by distance limit 25" % {'lat': float(lat), 'lng': float(lng)}
    blips = Blip.query().from_statement(query).all()
    return jsonify(API_Response("OK",[blip.serialize for blip in blips]).as_dict())
  elif 'id' in request.args:
    blip_id = request.args['id']
    blip = Blip.query.filter_by(id=blip_id).first()
    if blip:
      return jsonify(API_Response("OK", [blip.serialize]).as_dict())
    else:
      return jsonify(API_Response("ERR", [], "No blip with that ID").as_dict())
  else:
    blips = Blip.query.all()
    return jsonify(API_Response("OK",[blip.serialize for blip in blips]).as_dict())


@app.route("/api/blip", methods=['PUT'])
def create_blip():
  try:
    if all ([arg in request.form for arg in
             ['song_id','longitude',
                    'latitude','user_id','password']]):
      usr = User.query.filter_by(id=request.form['user_id']).first()
      if usr.check_password(request.form['password']):
        new_blip = Blip(request.form['song_id'],  
                        request.form['user_id'],
                        request.form['longitude'],
                        request.form['latitude'])
        db.session.add(new_blip)  
        db.session.commit()
        return jsonify(API_Response("OK", [new_blip.serialize]).as_dict())
      else:
        raise Exception
    else:
      raise Exception
  except Exception as e:
    return jsonify(API_Response("ERR", [], str(e)).as_dict())
  return None

@app.route("/api/song",methods=['PUT'])
def create_song():
  try:
    if all([arg in request.form for arg in
            ['artist','album','title',
            'provider_key','provider_song_id']]):
      new_song = Song(request.form['artist'], request.form['title'],
                      request.form['album'], request.form['provider_song_id'],
                      request.form['provider_key']))
      db.session.add(new_song)
      db.session.commit()
      return jsonify(API_Response("OK", [new_song.serialize]).as_dict())
    else:
      raise Exception
  except Exception as e:
    return jsonify(API_Response("ERR", [], str(e)).as_dict())
  return None


# MODEL DEFINITIONS
class User(db.Model):
  __tablename__ = 'user'

  id      = db.Column(db.Integer, primary_key = True)
  name    = db.Column(db.String(80), unique = True)
  email   = db.Column(db.String(120), unique = True)
  pw_hash = db.Column(db.String(120))
  blip    = db.relationship("Blip", backref="user")

  def __init__(self, name, email, password):
    self.name = name
    self.email = email
    self.set_password(password)

  def set_password(self, password):
    self.pw_hash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.pw_hash, password)

  @property
  def serialize(self):
    """Return object data in easily serializeable format"""
    return {
      'id' : self.id,
      'name' : self.name,
      'email' :self.email,
    }

class Song(db.Model):
  __tablename__ = 'song'

  id               = db.Column(db.Integer, primary_key = True)
  artist           = db.Column(db.String(80))
  title            = db.Column(db.String(120))
  album            = db.Column(db.String(80))
  provider_song_id = db.Column(db.String(200))
  provider_key     = db.Column(db.Enum('Spotify','Youtube',
                                       name='provider_key'))
  blip             = db.relationship("Blip", backref="song")

  def __init__(self, artist, title, album, provider_song_id, provider_key):
    self.artist = artist
    self.title  = title
    self.album  = album
    self.provider_song_id = provider_song_id
    self.provider_key = provider_key

  @property
  def serialize(self):
    return {
      'id'               : self.id,
      'artist'           : self.artist,
      'title'            : self.title,
      'album'            : self.album,
      'provider_song_id' : self.provider_song_id,
      'provider_key'     : str(self.provider_key)
    }


class Blip(db.Model):
  __tablename__ = 'blip'

  id        = db.Column(db.Integer, primary_key = True)
  song_id   = db.Column(db.Integer, db.ForeignKey('song.id'))
  user_id   = db.Column(db.Integer, db.ForeignKey('user.id'))
  longitude = db.Column(db.Float)
  latitude  = db.Column(db.Float)
  timestamp = db.Column(db.DateTime, default=datetime.now)

  def __init__(self, song_id, user_id, longitude, latitude):
    self.song_id   = song_id
    self.user_id   = user_id
    self.longitude = longitude
    self.latitude  = latitude

  @property
  def serialize(self):
    song = Song.query.filter_by(id=self.song_id).first()
    return {
      'id'        : self.id,
      'song'      : song.serialize,
      'user_id'   : self.user_id,
      'longitude' : self.longitude,
      'latitude'  : self.latitude,
      'timestamp' : dump_datetime(self.timestamp)
    }

# MAIN RUN

if __name__ == "__main__":
  # Bind to PORT if defined, otherwise default to 5000.
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)

