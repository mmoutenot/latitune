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
  def as_json(self):
    return jsonify(self.as_dict())

# Decorator declarations

import functools

def check_arguments(names):
  def wrap(fn):
    @functools.wraps(fn)
    def wrapped_fn():
      if all ([arg in request.values for arg in names]):
        return fn()
      else:
        return API_Response("ERR", [], "Missing Required Parameters").as_json()
    return wrapped_fn
  return wrap

def require_authentication(fn):
  @functools.wraps(fn)
  def wrap():
    user_fields = ['user_id', 'username']
    u_field = [u_f for u_f in user_fields if u_f in request.values][0]
    if u_field and not all ([arg in request.values for arg in [u_field, 'password']]):
      return API_Response("ERR", [], "Missing Required Parameters").as_json()
    else:
      if u_field == 'user_id':
        user = User.query.filter_by(id=request.values[u_field]).first()
      elif u_field == 'username':
        user = User.query.filter_by(name=request.values[u_field]).first()
      if not user or not user.check_password(request.values['password']):
        return API_Response("ERR", [], "Invalid Authentication").as_json()
      return fn()
  return wrap

# DEVELOPMENT ONLY

@app.route("/api/tabularasa", methods=['GET'])
def destroy():
  if os.environ.get('LATITUNE_LOCAL') == "true":
    db.session.remove()
    db.drop_all()
    db.create_all()
    return "OK"
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
    return API_Response("OK", [new_user.serialize]).as_json()
  except Exception as e:
    return API_Response("ERR", [], "Username or email already exists").as_json()

@app.route("/api/user", methods=['GET'])
@require_authentication
def get_user_id():
  try:
    user = User.query.filter_by(name=request.args['username']).first()
    return API_Response("OK", [user.serialize]).as_json()
  except Exception as e:
    return API_Response("ERR", [], str(e)).as_json()

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
      return API_Response("OK",[blip.serialize for blip in blips]).as_json()
    elif 'id' in request.args:
      blip_id = request.args['id']
      blip = Blip.query.filter_by(id=blip_id).first()
      if blip:
        return API_Response("OK", [blip.serialize]).as_json()
      else:
        return API_Response("ERR", [], "No blip with that ID").as_json()
    else:
      blips = Blip.query.all()
      return API_Response("OK",[blip.serialize for blip in blips]).as_json()
  except Exception as e:
    return API_Response("ERR", [], str(e)).as_json()

@app.route("/api/blip", methods=['PUT'])
@check_arguments(['song_id','longitude', 'latitude','user_id','password'])
@require_authentication
def create_blip():
  try:
    usr  = User.query.get(request.form['user_id'])
    song = Song.query.get(request.form['song_id'])
    if not song:
      return API_Response("ERR", [], "Song ID does not exist").as_json()
    new_blip = Blip(request.form['song_id'],
                    request.form['user_id'],
                    request.form['longitude'],
                    request.form['latitude'])

    db.session.add(new_blip)
    db.session.commit()
    return API_Response("OK", [new_blip.serialize]).as_json()
  except Exception as e:
    return API_Response("ERR", [], str(e)).as_json()
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
    return API_Response("OK", [new_song.serialize]).as_json()
  except Exception as e:
    return API_Response("ERR", [], request.form).as_json()
  return None

@app.route("/api/blip/comment",methods=['PUT'])
@check_arguments(['user_id','blip_id','password','comment'])
@require_authentication
def create_comment():
  user = User.query.get(request.form['user_id'])
  blip = Blip.query.get(request.form['blip_id'])
  if not blip:
    return API_Response("ERR", [], "Blip ID does not exist").as_json()
  new_comment = Comment(request.form['user_id'],request.form['blip_id'],request.form['comment'])
  db.session.add(new_comment)
  db.session.commit()
  return API_Response("OK",[new_comment.serialize]).as_json()

@app.route("/api/blip/comment",methods=['GET'])
def get_comment():
  if 'id' in request.args:
    comment = Comment.query.filter_by(id=request.args['id']).first()
    if not comment:
      return API_Response("ERR", [], "Comment ID does not exist").as_json()
    return API_Response("OK",[comment.serialize]).as_json()
  if 'blip_id' in request.args:
    comments = Comment.query.filter_by(blip_id=request.args['blip_id']).order_by(db.desc('comment.timestamp')).all()
    return API_Response("OK",[comment.serialize for comment in comments]).as_json()
  return API_Response("ERR", [], "Missing Required Parameters").as_json()

@app.route("/api/blip/favorite",methods=['PUT'])
@check_arguments(['user_id','blip_id','password'])
@require_authentication
def create_favorite():
  user = User.query.get(request.form['user_id'])
  blip = Blip.query.get(request.form['blip_id'])
  if not blip:
    return API_Response("ERR", [], "Blip ID does not exist").as_json()
  existing = Favorite.query.filter_by(user_id=request.form['user_id'],blip_id=request.form['blip_id']).first()
  if not existing:
    new_favorite = Favorite(request.form['user_id'],request.form['blip_id'])
    db.session.add(new_favorite)
    db.session.commit()
    existing = new_favorite
  return API_Response("OK",[existing.serialize]).as_json()

@app.route("/api/blip/favorite",methods=["GET"])
def get_favorites():
  if "blip_id" in request.args:
    favorites = Favorite.query.filter_by(blip_id=request.args['blip_id']).order_by(db.desc("user_id")).all()
    objects = map(lambda x:User.query.get(x.user_id),favorites)
  if "user_id" in request.args:
    favorites = Favorite.query.filter_by(user_id=request.args['user_id']).order_by(db.asc("blip_id")).all()
    objects = map(lambda x:Blip.query.get(x.blip_id),favorites)
  return API_Response("OK",[] if objects == [] else [object.serialize for object in objects]).as_json()

@app.route("/api/blip/favorite",methods=["DELETE"])
@check_arguments(['user_id','blip_id','password'])
@require_authentication
def delete_favorite():
  favorite = Favorite.query.filter_by(blip_id=request.args['blip_id'],user_id=request.args['user_id'])
  user = User.query.get(request.args['user_id'])
  if favorite.first() is None:
    return API_Response("ERR", [], "Favorite does not exist").as_json()
  favorite.delete()
  db.session.commit()
  return API_Response("OK",[]).as_json()

