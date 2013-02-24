##################################################
# MODEL DEFINITIONS
##################################################

import os
import sys
from settings import *
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

groups_to_users_table = Table('groups_to_users', Base.metadata,
    Column('group_id', Integer, ForeignKey('group.id')),
    Column('user_id',  Integer, ForeignKey('user.id'))
)

posts_to_tags_table = Table('posts_to_tags', Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('tag_id',  Integer, ForeignKey('tag.id'))
)


class User(db.Model):
  __tablename__ = 'user'

  id      = db.Column(db.Integer, primary_key = True)
  name    = db.Column(db.String(80), unique = True)
  email   = db.Column(db.String(120), unique = True)
  pw_hash = db.Column(db.String(120))
  post    = db.relationship("Post", backref="user")

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

class Post(db.Model):
  __tablename__ = 'post'

  id         = db.Column(db.Integer, primary_key = True)
  kind       = db.Column(db.String(80))
  url        = db.Column(db.String(120))
  timestamp = db.Column(db.DateTime, default=datetime.now)
  group_id   = db.Column(db.Integer, db.ForeignKey('group.id'))
  user_id    = db.Column(db.Integer, db.ForeignKey('user.id'))
  tags       = db.relationship("Tag", secondary = posts_to_tags_table, backref = "post")

  def __init__(self, kind, url, group, user, tags):
    self.kind  = kind
    self.url   = url
    self.group = group
    self.user  = user
    self.tags  = tags

  @property
  def serialize(self):
    group = Group.query.filter_by(id=self.group_id).first()
    user  = Group.query.filter_by(id=self.user_id).first()
    return {
      'id'         : self.id,
      'kind'       : self.kind,
      'url'        : self.url,
      'date_added' : self.date_added,
      'group'      : group.serialize,
      'user'       : user.serialize,
      'tags'       : str(self.tags)
    }


class Group(db.Model):
  __tablename__ = 'group'

  id        = db.Column(db.Integer, primary_key = True)
  users     = db.relationship("User", secondary = groups_to_users_table, backref = "group")
  posts     = db.relationship("Post", backref = "group")

  def __init__(self, users, posts):
    self.users = users
    self.posts = posts

  @property
  def serialize(self):
    song = Song.query.filter_by(id=self.song_id).first()
    return {
      'id' : self.id,
      'users' : [user.serialize for user in users],
      'posts' : [post.serialize for post in posts]
    }

class Tag(db.Model):
  __tablename__ = 'tag'

  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(20))

# class Comment(db.Model):
#   __tablename__ = "comment"
#
#   id        = db.Column(db.Integer, primary_key = True)
#   blip_id   = db.Column(db.Integer, db.ForeignKey('blip.id'))
#   user_id   = db.Column(db.Integer, db.ForeignKey('user.id'))
#   comment   = db.Column(db.Text)
#   timestamp = db.Column(db.DateTime, default=datetime.now)
#
#   def __init__(self, user_id,blip_id,comment):
#     self.user_id = user_id
#     self.blip_id = blip_id
#     self.comment = comment
#
#   @property
#   def serialize(self):
#     blip = Blip.query.filter_by(id=self.blip_id).first()
#     return {
#       'id'       : self.id,
#       'blip'     : blip.serialize,
#       'comment'  : self.comment,
#       'user_id'  : self.user_id,
#       'timestamp': self.timestamp.isoformat()
#     }

