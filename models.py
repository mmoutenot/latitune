##################################################
# MODEL DEFINITIONS
##################################################

import os
import sys
from settings import *
from datetime import datetime

class User(db.Model):
  __tablename__ = 'user'

  id      = db.Column(db.Integer, primary_key = True)
  first_name    = db.Column(db.String(120))
  last_name  = db.Column(db.String(120))
  rdio_key = db.Column(db.String(50), unique=True)
  url = db.Column(db.String(120))
  icon = db.Column(db.String(120))
  email = db.Column(db.String(120))
  blip    = db.relationship("Blip", backref="user")

  def __init__(self, first_name, last_name, email, rdio_key, url, icon):
    self.first_name = first_name
    self.last_name = last_name
    self.rdio_key = rdio_key
    self.url = url
    self.icon = icon
    self.email = email

  @property
  def serialize(self):
    """Return object data in easily serializeable format"""
    return {
      'id' : self.id,
      'name' : self.first_name + " " +  self.last_name,
      'rdio_key' : self.rdio_key,
      'url': self.url,
      'icon' : self.icon
    }

class Song(db.Model):
  __tablename__ = 'song'

  id               = db.Column(db.Integer, primary_key = True)
  artist           = db.Column(db.String(80))
  title            = db.Column(db.String(120))
  album            = db.Column(db.String(80))
  echonestID       = db.Column(db.String(20))
  blip             = db.relationship("Blip", backref="song")
  providers        = db.relationship("SongProvider")

  def __init__(self, artist, title, echonest_id, album=""):
    self.artist = artist
    self.title  = title
    self.album  = album
    self.echonestID = echonest_id

  @property
  def serialize(self):
    return {
      'id'               : self.id,
      'artist'           : self.artist,
      'title'            : self.title,
      'album'            : self.album,
      'echonestID'       : self.echonestID,
      'providers'        : [p.serialize for p in self.providers]
    }

class SongProvider(db.Model):
  __tablename__ = "song_provider"

  id = db.Column(db.Integer, primary_key = True)
  song_id = db.Column(db.Integer, db.ForeignKey('song.id'))
  provider = db.Column(db.Enum("Rdio", "Spotify", name="provider"))
  provider_key = db.Column(db.String(50))

  def __init__(self, song_id, provider, provider_key):
    self.song_id = song_id
    self.provider = provider
    self.provider_key = provider_key

  @property
  def serialize(self):
    return {
      'provider':self.provider,
      'provider_key':self.provider_key
    }  

class Blip(db.Model):
  __tablename__ = 'blip'

  id        = db.Column(db.Integer, primary_key = True)
  song_id   = db.Column(db.Integer, db.ForeignKey('song.id'))
  user_id   = db.Column(db.Integer, db.ForeignKey('user.id'))
  longitude = db.Column(db.Float)
  latitude  = db.Column(db.Float)
  timestamp = db.Column(db.DateTime, default=datetime.now)

  def __init__(self, song_id, user, longitude, latitude):
    self.song_id   = song_id
    self.user_id   = user.id
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

  def __init__(self, user, blip_id, comment):
    self.user_id = user.id
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

class Favorite(db.Model):
  __tablename__ = "favorite"

  id      = db.Column(db.Integer, primary_key = True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  blip_id = db.Column(db.Integer, db.ForeignKey('blip.id'))

  def __init__(self, user, blip_id):
    self.user_id = user.id
    self.blip_id = blip_id

  @property 
  def serialize(self):
    return {
      'id'     : self.id,
      'user_id': self.user_id,
      'blip_id': self.blip_id
    }