##################################################
# CONTROLLERS
##################################################
from flask import Flask, jsonify, request
from sqlalchemy.exc import IntegrityError
from settings import *
from models import *
from pyechonest import song

MISSING_PARAMETERS      = 10
SUCCESS                 = 20
EMAIL_EXISTS            = 30
USER_EXISTS             = 31
INVALID_AUTH            = 32
USER_DOES_NOT_EXIST     = 33
SONG_DOES_NOT_EXIST     = 40
BLIP_DOES_NOT_EXIST     = 50
COMMENT_DOES_NOT_EXIST  = 60
FAVORITE_DOES_NOT_EXIST = 70

STATUS_CODE_MESSAGES = {
  MISSING_PARAMETERS      : "Missing Required Parameters",
  SUCCESS                 : "Success",
  EMAIL_EXISTS            : "Email already exists",
  USER_EXISTS             : "User already exists",
  INVALID_AUTH            : "Invalid Authentication",
  USER_DOES_NOT_EXIST     : "User does not exist",
  SONG_DOES_NOT_EXIST     : "Song ID does not exist",
  BLIP_DOES_NOT_EXIST     : "Blip ID does not exist",
  COMMENT_DOES_NOT_EXIST  : "Comment ID does not exist",
  FAVORITE_DOES_NOT_EXIST : "Favorite ID does not exist",
  "ERR"                   : "You fucked up"
}

##
# Helper to build json responses for API endpoints
##
class API_Response:
  def __init__(self,status=SUCCESS, objs=[], error=""):
   self.status = status
   self.error  = STATUS_CODE_MESSAGES[status]
   self.objs   = objs

  def as_dict(self):
    if self.status != SUCCESS:
      return {"meta"    : {"status":self.status,"error":self.error},
              "objects" : self.objs}
    else:
      return {"meta"    : {"status":self.status},"objects":self.objs}

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
        return API_Response(MISSING_PARAMETERS).as_json()
    return wrapped_fn
  return wrap

def require_authentication(fn):
  @functools.wraps(fn)
  def wrap():
    user_fields = ['rdio_key']
    if len([u_f for u_f in user_fields if u_f in request.values]) == 0:
      return API_Response(MISSING_PARAMETERS).as_json()
    user = User.query.filter_by(rdio_key=request.values['rdio_key']).first()
    if not user:
      return API_Response(USER_DOES_NOT_EXIST).as_json()
    return fn(user)
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
@check_arguments(['first_name', 'last_name', 'email', 'rdio_key', 'url', 'icon'])
def create_user():
  try:
    new_user = User(request.form['first_name'],
                    request.form['last_name'],
                    request.form['email'],
                    request.form['rdio_key'],
                    request.form['url'],
                    request.form['icon'])
    db.session.add(new_user)
    db.session.commit()
    return API_Response(SUCCESS, [new_user.serialize]).as_json()
  except IntegrityError as e:
    db.session.rollback()
    if User.query.filter_by(rdio_key=request.form['rdio_key']).first() is not None:
      return API_Response(USER_EXISTS).as_json()

@app.route("/api/user", methods=['GET'])
@require_authentication
def get_user_id(user):
  try:
    return API_Response(SUCCESS, [user.serialize]).as_json()
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
      return API_Response(SUCCESS,[blip.serialize for blip in blips]).as_json()
    elif 'id' in request.args:
      blip_id = request.args['id']
      blip = Blip.query.filter_by(id=blip_id).first()
      if blip:
        return API_Response(SUCCESS, [blip.serialize]).as_json()
      else:
        return API_Response("ERR", []).as_json()
    else:
      blips = Blip.query.all()
      return API_Response(SUCCESS,[blip.serialize for blip in blips]).as_json()
  except Exception as e:
    return API_Response("ERR", [], str(e)).as_json()

@app.route("/api/blip", methods=['PUT'])
@check_arguments(['song_id','longitude', 'latitude'])
@require_authentication
def create_blip(user):
  try:
    song = Song.query.get(request.form['song_id'])
    if not song:
      return API_Response(SONG_DOES_NOT_EXIST).as_json()
    new_blip = Blip(request.form['song_id'],
                    user,
                    request.form['longitude'],
                    request.form['latitude'])

    db.session.add(new_blip)
    db.session.commit()
    return API_Response(SUCCESS, [new_blip.serialize]).as_json()
  except Exception as e:
    return API_Response("ERR", [], str(e)).as_json()
  return None

# SONG

@app.route("/api/song",methods=['PUT'])
@check_arguments(['artist','title','echonest_id','album'])
def create_song():
  try:
    new_song = Song.query.filter_by(artist=request.form['artist'],
                                    title=request.form['title']).first()
    if not new_song:
      new_song = Song(request.form['artist'], request.form['title'], request.form['echonest_id'],request.form['album'])
      db.session.add(new_song)
      db.session.commit()
      ss_results = song.profile(ids=new_song.echonestID, buckets=['id:rdio-US','id:spotify-WW'])
      for ensong in ss_results:
        for rdioTrack in ensong.get_tracks('rdio-US'):
          trackID = rdioTrack["foreign_id"].split(":")[2]
          new_songprovider = SongProvider(new_song.id, "Rdio", trackID)
          db.session.add(new_songprovider)
        for spotifyTrack in ensong.get_tracks('spotify-WW'):
          trackID = spotifyTrack["foreign_id"].split(":")[2]
          new_songprovider = SongProvider(new_song.id, "Spotify", trackID)
          db.session.add(new_songprovider)
      db.session.commit()
    return API_Response(SUCCESS, [new_song.serialize]).as_json()
  except Exception as e:
    print e
    return API_Response("ERR", [], request.form).as_json()
  return None

@app.route("/api/blip/comment",methods=['PUT'])
@check_arguments(['blip_id','comment'])
@require_authentication
def create_comment(user):
  blip = Blip.query.get(request.form['blip_id'])
  if not blip:
    return API_Response(BLIP_DOES_NOT_EXIST).as_json()
  new_comment = Comment(user,request.form['blip_id'],request.form['comment'])
  db.session.add(new_comment)
  db.session.commit()
  return API_Response(SUCCESS,[new_comment.serialize]).as_json()

@app.route("/api/blip/comment",methods=['GET'])
def get_comment():
  if 'id' in request.args:
    comment = Comment.query.filter_by(id=request.args['id']).first()
    if not comment:
      return API_Response(COMMENT_DOES_NOT_EXIST).as_json()
    return API_Response(SUCCESS,[comment.serialize]).as_json()
  if 'blip_id' in request.args:
    comments = Comment.query.filter_by(blip_id=request.args['blip_id']).order_by(db.desc('comment.timestamp')).all()
    return API_Response(SUCCESS,[comment.serialize for comment in comments]).as_json()
  return API_Response(MISSING_PARAMETERS).as_json()

@app.route("/api/blip/favorite",methods=['PUT'])
@check_arguments(['blip_id'])
@require_authentication
def create_favorite(user):
  blip = Blip.query.get(request.form['blip_id'])
  if not blip:
    return API_Response(BLIP_DOES_NOT_EXIST).as_json()
  existing = Favorite.query.filter_by(user=user,blip_id=request.form['blip_id']).first()
  if not existing:
    new_favorite = Favorite(request.form['rdio_key'],request.form['blip_id'])
    db.session.add(new_favorite)
    db.session.commit()
    existing = new_favorite
  return API_Response(SUCCESS,[existing.serialize]).as_json()

@app.route("/api/blip/favorite",methods=["GET"])
def get_favorites():
  if "blip_id" in request.args:
    favorites = Favorite.query.filter_by(blip_id=request.args['blip_id']).order_by(db.desc("rdio_key")).all()
    objects = map(lambda x:User.query.get(x.rdio_key),favorites)
  if "rdio_key" in request.args:
    favorites = Favorite.query.filter_by(rdio_key=request.args['rdio_key']).order_by(db.asc("blip_id")).all()
    objects = map(lambda x:Blip.query.get(x.blip_id),favorites)
  return API_Response(SUCCESS,[] if objects == [] else [object.serialize for object in objects]).as_json()

@app.route("/api/blip/favorite",methods=["DELETE"])
@check_arguments(['blip_id'])
@require_authentication
def delete_favorite(user):
  favorite = Favorite.query.filter_by(blip_id=request.args['blip_id'],rdio_key=request.args['rdio_key'])
  if favorite.first() is None:
    return API_Response(FAVORITE_DOES_NOT_EXIST).as_json()
  favorite.delete()
  db.session.commit()
  return API_Response(SUCCESS).as_json()

