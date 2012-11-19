##################################################
# MODEL DEFINITIONS
##################################################

import os
import sys
from settings import *
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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

class Comment(db.Model):
  __tablename__ = "comment"

  id = db.Column(db.Integer, primary_key = True)
  blip_id   = db.Column(db.Integer, db.ForeignKey('blip.id'))
  user_id   = db.Column(db.Integer, db.ForeignKey('user.id'))
  comment   = db.Column(db.Text)
  timestamp = db.Column(db.DateTime, default=datetime.now)

  def __init__(self, user_id,blip_id,comment):
    self.user_id = user_id
    self.blip_id = blip_id
    self.comment = comment

  @property
  def serialize(self):
    blip = Blip.query.filter_by(id=self.blip_id).first()
    return {
      'id'       : self.id,
      'blip'     : blip.serialize,
      'comment'  : self.comment,
      'user_id'  : self.user_id,
      'timestamp': self.timestamp.isoformat()
    }