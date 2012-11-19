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

@app.route("/api/comment",methods=['PUT'])
def create_comment():
  if not all([arg in request.form for arg in ['user_id','blip_id','password','comment']]):
    return jsonify(API_Response("ERR", [], "Missing Required Parameters").as_dict())
  user = User.query.get(request.form['user_id'])
  blip = Blip.query.get(request.form['blip_id'])
  if not blip:
    return jsonify(API_Response("ERR", [], "Blip ID does not exist").as_dict())
  if not user:
    return jsonify(API_Response("ERR", [], "User ID does not exist").as_dict())
  if not user.check_password(request.form['password']):
        return jsonify(API_Response("ERR", [], "Invalid Authentication").as_dict())


  new_comment = Comment(request.form['user_id'],request.form['blip_id'],request.form['comment'])
  db.session.add(new_comment)
  db.session.commit()
  return jsonify(API_Response("OK",[new_comment.serialize]).as_dict())

@app.route("/api/comment",methods=['GET'])
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