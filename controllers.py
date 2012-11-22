##################################################
# CONTROLLERS
##################################################
from flask import Flask, jsonify, request
from settings import *
from models import *

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

# Decorator declarations

import functools

def check_arguments(names):
  def wrap(fn):
    @functools.wraps(fn)
    def wrapped_fn():
      if all ([arg in request.values for arg in names]):
        return fn()
      else:
        return jsonify(API_Response("ERR", [], "Missing Required Parameters").as_dict())
    return wrapped_fn
  return wrap

def require_authentication(fn):
  @functools.wraps(fn)
  def wrap():
    user_fields = ['user_id', 'username']
    u_field = [u_f for u_f in user_fields if u_f in request.values][0]
    if u_field and not all ([arg in request.values for arg in [u_field, 'password']]):
      return jsonify(API_Response("ERR", [], "Missing Required Parameters").as_dict())
    else:
      if u_field == 'user_id':
        user = User.query.filter_by(id=request.values[u_field]).first()
      elif u_field == 'username':
        user = User.query.filter_by(name=request.values[u_field]).first()
      if not user or not user.check_password(request.values['password']):
        return jsonify(API_Response("ERR", [], "Invalid Authentication").as_dict())
      return fn()
  return wrap

# DEVELOPMENT ONLY

@app.route("/api/tabularasa", methods=['GET'])
def destroy():
  if os.environ.get('LATITUNE_LOCAL') == "true":
    db.session.remove()
    db.drop_all()
    db.create_all()
    return "TABULA RASA, BITCH"
  return "WHO DO YOU THINK YOU ARE?"

# USER

@app.route("/api/user", methods=['PUT'])
@check_arguments(['username','email','password'], )
def create_user():
  try:
    new_user = User(request.form['username'],
                    request.form['email'],
                    request.form['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify(API_Response("OK", [new_user.serialize]).as_dict())
  except Exception as e:
    return jsonify(API_Response("ERR", [], "Username or email already exists").as_dict())

@app.route("/api/user", methods=['GET'])
@require_authentication
def get_user_id():
  try:
    user = User.query.filter_by(name=request.args['username']).first()
    return jsonify(API_Response("OK", [user.serialize]).as_dict())
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
@check_arguments(['song_id','longitude', 'latitude','user_id','password'])
@require_authentication
def create_blip():
  try:
    usr  = User.query.get(request.form['user_id'])
    song = Song.query.get(request.form['song_id'])
    if not song:
      return jsonify(API_Response("ERR", [], "Song ID does not exist").as_dict())
    new_blip = Blip(request.form['song_id'],
                    request.form['user_id'],
                    request.form['longitude'],
                    request.form['latitude'])

    db.session.add(new_blip)
    db.session.commit()
    return jsonify(API_Response("OK", [new_blip.serialize]).as_dict())
  except Exception as e:
    return jsonify(API_Response("ERR", [], str(e)).as_dict())
  return None

# SONG

@app.route("/api/song",methods=['PUT'])
@check_arguments(['artist','title'])
def create_song():
  try:
    new_song = Song.query.filter_by(artist=request.form['artist'],
                                    title=request.form['title']).first()
    if not new_song:
      new_song = Song(request.form['artist'], request.form['title'])
      db.session.add(new_song)
      db.session.commit()
    return jsonify(API_Response("OK", [new_song.serialize]).as_dict())
  except Exception as e:
    return jsonify(API_Response("ERR", [], request.form).as_dict())
  return None

@app.route("/api/blip/comment",methods=['PUT'])
@check_arguments(['user_id','blip_id','password','comment'])
@require_authentication
def create_comment():
  user = User.query.get(request.form['user_id'])
  blip = Blip.query.get(request.form['blip_id'])
  if not blip:
    return jsonify(API_Response("ERR", [], "Blip ID does not exist").as_dict())
  new_comment = Comment(request.form['user_id'],request.form['blip_id'],request.form['comment'])
  db.session.add(new_comment)
  db.session.commit()
  return jsonify(API_Response("OK",[new_comment.serialize]).as_dict())

@app.route("/api/blip/comment",methods=['GET'])
def get_comment():
  if 'id' in request.args:
    comment = Comment.query.filter_by(id=request.args['id']).first()
    if not comment:
      return jsonify(API_Response("ERR", [], "Comment ID does not exist").as_dict())
    return jsonify(API_Response("OK",[comment.serialize]).as_dict())
  if 'blip_id' in request.args:
    comments = Comment.query.filter_by(blip_id=request.args['blip_id']).order_by(db.desc('comment.timestamp')).all()
    return jsonify(API_Response("OK",[comment.serialize for comment in comments]).as_dict())
  return jsonify(API_Response("ERR", [], "Missing Required Parameters").as_dict())

@app.route("/api/blip/favorite",methods=['PUT'])
def create_favorite():
  if not all([arg in request.form for arg in ['user_id','blip_id','password']]):
    return jsonify(API_Response("ERR", [], "Missing Required Parameters").as_dict())
  user = User.query.get(request.form['user_id'])
  blip = Blip.query.get(request.form['blip_id'])
  if not blip:
    return jsonify(API_Response("ERR", [], "Blip ID does not exist").as_dict())
  if not user:
    return jsonify(API_Response("ERR", [], "User ID does not exist").as_dict())
  if not user.check_password(request.form['password']):
        return jsonify(API_Response("ERR", [], "Invalid Authentication").as_dict())
  existing = Favorite.query.filter_by(user_id=request.form['user_id'],blip_id=request.form['blip_id']).first()
  if not existing:
    new_favorite = Favorite(request.form['user_id'],request.form['blip_id'])
    db.session.add(new_favorite)
    db.session.commit()
    existing = new_favorite
  return jsonify(API_Response("OK",[existing.serialize]).as_dict())

@app.route("/api/blip/favorite",methods=["GET"])
def get_favorites():
  if "blip_id" in request.args:
    favorites = Favorite.query.filter_by(blip_id=request.args['blip_id']).order_by(db.desc("user_id")).all()
    objects = map(lambda x:User.query.get(x.user_id),favorites)
  if "user_id" in request.args:
    favorites = Favorite.query.filter_by(user_id=request.args['user_id']).order_by(db.asc("blip_id")).all()
    objects = map(lambda x:Blip.query.get(x.blip_id),favorites)
  return jsonify(API_Response("OK",[] if objects == [] else [object.serialize for object in objects]).as_dict())

@app.route("/api/blip/favorite",methods=["DELETE"])
def delete_favorite():
  if not all([arg in request.args for arg in ['user_id','blip_id','password']]):
    return jsonify(API_Response("ERR", [], "Missing Required Parameters").as_dict())
  favorite = Favorite.query.filter_by(blip_id=request.args['blip_id'],user_id=request.args['user_id'])
  user = User.query.get(request.args['user_id'])
  if not user.check_password(request.args['password']):
    return jsonify(API_Response("ERR", [], "Invalid Authentication").as_dict())
  if favorite.first() is None:
    return jsonify(API_Response("ERR", [], "Favorite does not exist").as_dict())
  favorite.delete()
  db.session.commit()
  return jsonify(API_Response("OK",[]).as_dict())

