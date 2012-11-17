import os
import sys
from datetime import datetime
from flask import Flask, jsonify, request
from flask_heroku import Heroku
from flask.ext.sqlalchemy import SQLAlchemy

# for password hashing
from werkzeug.security import generate_password_hash, check_password_hash

# for youtube song matching
import gdata.youtube
import gdata.youtube.service

yt_service = gdata.youtube.service.YouTubeService()
yt_service.developer_key = 'AI39si4fdpqYBz4_a6E7choIqT5hIlYhbI4Ucp5eiXGDt5jzE46XM_KxWn5KtwdrAZp6WeMF9Jrzk-sXabs0R_F9T9MHZdiOYA'

app       = Flask (__name__)
if os.environ.get('LATITUNE_LOCAL') == "true":
  app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/latitune_dev'
else:
  heroku    = Heroku(app)
app.debug = True

heroku = None
db        = SQLAlchemy (app)

##
# Helper to build json responses for API endpoints
##
class API_Response:
  def __init__(self, status="ERR", objs=[], error=""):
   self.status = status
   self.error  = error
   self.objs   = objs

  def as_dict(self):
    return {"meta"    : {"status":self.status,"error":self.error},
            "objects" : self.objs}

##################################################
# CONTROLLERS
##################################################

# USER

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
      return jsonify(API_Response("ERR", [], "Missing required parameters").as_dict())
  except Exception as e:
    return jsonify(API_Response("ERR", [], "Username or email already exists").as_dict())

@app.route("/api/user", methods=['GET'])
def get_user_id():
  try:
    if all ([arg in request.args for arg in ['username','password']]):
      user = User.query.filter_by(name=request.args['username']).first()
      if not user or not user.check_password(request.args['password']):
        return jsonify(API_Response("ERR", [], "Invalid Authentication").as_dict())
      # user is properly authenticated!
      return jsonify(API_Response("OK", [user.serialize]).as_dict())
    else:
      return jsonify(API_Response("ERR", [], "Missing required parameters").as_dict())
  except Exception as e:
    return jsonify(API_Response("ERR", [], str(e)).as_dict())

# BLIPS

@app.route("/api/blip", methods=['GET'])
def get_blip():
  try:
    if all([arg in request.args for arg in ['latitude','longitude']]):
      lat = request.args['latitude']
      lng = request.args['longitude']
      db.session.commit()
      query = """
        SELECT id, longitude, latitude,
          (3959*ACOS(COS(RADIANS(%(lat)i))*COS(RADIANS(latitude))*COS(RADIANS(longitude)-RADIANS(%(lng)i))+SIN(RADIANS(%(lat)i))*SIN(RADIANS(latitude))))
        AS distance from blip
        order by distance asc limit 25""" % {'lat': float(lat), 'lng': float(lng)}
      blips = Blip.query.from_statement(query).all()
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
  except Exception as e:
    return jsonify(API_Response("ERR", [], str(e)).as_dict())

@app.route("/api/blip", methods=['PUT'])
def create_blip():
  try:
    if all ([arg in request.form for arg in ['song_id','longitude', 'latitude','user_id','password']]):
      usr  = User.query.get(request.form['user_id'])
      song = Song.query.get(request.form['song_id'])

      if not song:
        return jsonify(API_Response("ERR", [], "Song ID does not exist").as_dict())
      if not usr:
        return jsonify(API_Response("ERR", [], "User ID does not exist").as_dict())
      if not usr.check_password(request.form['password']):
        return jsonify(API_Response("ERR", [], "Invalid Authentication").as_dict())

      new_blip = Blip(request.form['song_id'],
                      request.form['user_id'],
                      request.form['longitude'],
                      request.form['latitude'])

      db.session.add(new_blip)
      db.session.commit()
      return jsonify(API_Response("OK", [new_blip.serialize]).as_dict())

    else:
      return jsonify(API_Response("ERR", [], "Missing Required Parameters").as_dict())
  except Exception as e:
    return jsonify(API_Response("ERR", [], str(e)).as_dict())
  return None

# SONG

@app.route("/api/song",methods=['PUT'])
def create_song():
  try:
    if all([arg in request.form for arg in ['artist','title']]):
      new_song = Song.query.filter_by(artist=request.form['artist'],
                                      title=request.form['title']).first()
      if not new_song:
        new_song = Song(request.form['artist'], request.form['title'])
        db.session.add(new_song)
        db.session.commit()
      return jsonify(API_Response("OK", [new_song.serialize]).as_dict())
    else:
      return jsonify(API_Response("ERR", [], "Missing Required Parameters").as_dict())
  except Exception as e:
    return jsonify(API_Response("ERR", [], request.form).as_dict())
  return None

##################################################
# MODEL DEFINITIONS
##################################################

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

  def __init__(self, artist, title, album="", provider_key="Youtube"):
    self.artist = artist
    self.title  = title
    self.album  = album

    query = gdata.youtube.service.YouTubeVideoQuery()
    query.vq = title + " " + artist
    query.orderby = 'relevance'
    query.racy = 'include'
    feed = yt_service.YouTubeQuery(query)
    entry = feed.entry[0]
    self.provider_song_id = entry.id.text.split('/')[-1]

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
      'timestamp' : self.timestamp.isoformat()
    }

# MAIN RUN

if __name__ == "__main__":
  # Bind to PORT if defined, otherwise default to 5000.
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)

