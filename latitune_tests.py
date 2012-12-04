import os
import latitune
import unittest
import tempfile
from datetime import datetime
import ast

class latituneTestCase(unittest.TestCase):

  """
  Helper functions
  """

  def createUser(self, username,password,email):
    return self.app.put("/api/user",data=dict(
        username=username,
        password=password,
        email=email
      ))

  def generateUser(self,username="ben",password="testpass",email="benweitzman@gmail.com"):
    userResponse = self.createUser(username,password,email)
    userDict = ast.literal_eval(userResponse.data)['objects'][0]
    return userDict

  def createSong(self,artist,title):
    return self.app.put("/api/song",data=dict(
        artist = artist,
        title  = title,
      ))

  def generateSong(self,artist="The Kinks",title="Big Sky"):
    songResponse = self.createSong(artist,title)
    songDict = ast.literal_eval(songResponse.data)['objects'][0]
    return songDict

  def createBlip(self,latitude,longitude,song_id,user_id,password):
    return self.app.put("/api/blip",data=dict(
        song_id   = song_id,
        longitude = longitude,
        latitude  = latitude,
        user_id   = user_id,
        password  = password,
      ))

  def generateBlip(self,latitude="50.0",longitude="50.0",username="ben",password="testpass",
                   email="benweitzman@gmail.com",artist="The Kinks",title="Big Sky"):
    userDict = self.generateUser(username=username,password=password,email=email)
    songDict = self.generateSong(artist=artist,title=title)
    blipResponse = self.createBlip(latitude,longitude,songDict['id'],userDict['id'],password)
    blipDict = ast.literal_eval(blipResponse.data)['objects'][0]
    return userDict, songDict, blipDict

  def createComment(self,user_id,password,blip_id,comment):
    return self.app.put("/api/blip/comment",data=dict(
        blip_id  = blip_id,
        user_id  = user_id,
        password = password,
        comment  = comment
      ))

  def generateComment(self,latitude="50.0",longitude="50.0",username="ben",password="testpass",
                      email="benweitzman@gmail.com",artist="The Kinks",title="Big Sky",
                      comment="This is a comment"):
    userDict, songDict, blipDict = self.generateBlip(latitude=latitude,longitude=longitude,username=username,password=password,
                                                     email=email,artist=artist,title=title)
    commentResponse = self.createComment(userDict['id'],password,blipDict['id'],comment)
    commentDict = ast.literal_eval(commentResponse.data)['objects'][0]
    return userDict, songDict, blipDict, commentDict

  def createFavorite(self,user_id,password,blip_id):
    return self.app.put("/api/blip/favorite", data=dict(
      user_id  = user_id,
      password = password,
      blip_id  = blip_id
    ))

  """
  Test stuff
  """

  def setUp(self):
    latitune.db.create_all()
    self.app = latitune.app.test_client()

  def tearDown(self):
    latitune.db.session.remove()
    latitune.db.drop_all()

  def test_db_sets_up(self):
    user = latitune.User("ben","benweitzman@gmail.com","testpass")
    latitune.db.session.add(user)
    latitune.db.session.commit()
    assert (latitune.User.query.first().name == "ben")

  """
  Model Tests
  """
  """ User """

  def test_user_constructor_applies_fields(self):
    user = latitune.User("ben","benweitzman@gmail.com","testpass")
    assert user.name == "ben"
    assert user.email == "benweitzman@gmail.com"

  def test_user_password_hashes(self):
    user = latitune.User("ben","benweitzman@gmail.com","testpass")
    assert user.check_password("testpass")

  def test_user_serializes(self):
    user = latitune.User("ben","benweitzman@gmail.com","testpass")
    latitune.db.session.add(user)
    latitune.db.session.commit()
    assert user.serialize == {"id":1,"name":"ben","email":"benweitzman@gmail.com"}

  """ Song """

  def test_song_constructor_applies_fields(self):
    song = latitune.Song("The Kinks","Big Sky")
    assert song.artist == "The Kinks"
    assert song.title == "Big Sky"
    assert song.provider_song_id == "wiyrFSSG5_g"
    assert song.provider_key == "Youtube"

  def test_song_serializes(self):
    song = latitune.Song("The Kinks","Big Sky")
    latitune.db.session.add(song)
    latitune.db.session.commit()
    serialized = song.serialize
    assert serialized == {"id":1,"artist":"The Kinks","title":"Big Sky","album":"","provider_key":"Youtube","provider_song_id":"wiyrFSSG5_g"}

  """ Blip """

  def test_blip_constructor_applies_fields(self):
    user = latitune.User("ben","benweitzman@gmail.com","testpass")
    latitune.db.session.add(user)
    song = latitune.Song("The Kinks","Big Sky")
    latitune.db.session.add(song)
    latitune.db.session.commit()
    blip = latitune.Blip(song.id, user.id, 50.0, 50.0)
    assert blip.song_id   == song.id
    assert blip.user_id   == user.id
    assert blip.latitude  == 50.0
    assert blip.longitude == 50.0

  def test_blip_serializes(self):
    user = latitune.User("ben","benweitzman@gmail.com","testpass")
    latitune.db.session.add(user)
    song = latitune.Song("The Kinks","Big Sky")
    latitune.db.session.add(song)
    latitune.db.session.commit()
    blip = latitune.Blip(song.id, user.id, 50.0, 50.0)

    now = datetime.now()
    blip.timestamp = now

    latitune.db.session.add(blip)
    latitune.db.session.commit()
    serialized = blip.serialize
    assert serialized == {"id":1, "song":song.serialize, "user_id":user.id,
                         "longitude":50.0, "latitude":50.0,
                         "timestamp":now.isoformat()}

  """ Comment """

  def test_comment_constructor_applies_fields(self):
    user = latitune.User("ben","benweitzman@gmail.com","testpass")
    latitune.db.session.add(user)
    song = latitune.Song("The Kinks","Big Sky")
    latitune.db.session.add(song)
    blip = latitune.Blip(song.id, user.id, 50.0, 50.0)
    latitune.db.session.add(blip)
    latitune.db.session.commit()
    comment = latitune.Comment(user.id,blip.id,"This is a comment")
    latitune.db.session.add(comment)
    latitune.db.session.commit()

    assert comment.user_id == user.id
    assert comment.blip_id == blip.id
    assert comment.comment == "This is a comment"

  def test_comment_serializes(self):
    user = latitune.User("ben","benweitzman@gmail.com","testpass")
    latitune.db.session.add(user)
    song = latitune.Song("The Kinks","Big Sky")
    latitune.db.session.add(song)
    latitune.db.session.commit()
    blip = latitune.Blip(song.id, user.id, 50.0, 50.0)
    latitune.db.session.add(blip)
    latitune.db.session.commit()
    comment = latitune.Comment(user.id,blip.id,"This is a comment")
    now = datetime.now()
    comment.timestamp = now
    latitune.db.session.add(comment)
    latitune.db.session.commit()

    serialized = comment.serialize
    assert serialized == {"id":1,"user_id":user.id,"blip":blip.serialize,"timestamp":now.isoformat(),"comment":"This is a comment"}

  """ Favorite """

  def test_favorite_constructor_applies_fields(self):
    user = latitune.User("ben","benweitzman@gmail.com","testpass")
    latitune.db.session.add(user)
    song = latitune.Song("The Kinks","Big Sky")
    latitune.db.session.add(song)
    blip = latitune.Blip(song.id, user.id, 50.0, 50.0)
    latitune.db.session.add(blip)
    latitune.db.session.commit()

    favorite = latitune.Favorite(user.id,blip.id)
    latitune.db.session.add(favorite)
    latitune.db.session.commit()

    assert favorite.user_id == user.id
    assert favorite.blip_id == blip.id

  def test_favorite_serializes(self):
    user = latitune.User("ben","benweitzman@gmail.com","testpass")
    latitune.db.session.add(user)
    song = latitune.Song("The Kinks","Big Sky")
    latitune.db.session.add(song)
    blip = latitune.Blip(song.id, user.id, 50.0, 50.0)
    latitune.db.session.add(blip)
    latitune.db.session.commit()

    favorite = latitune.Favorite(user.id,blip.id)
    latitune.db.session.add(favorite)
    latitune.db.session.commit()

    serialized = favorite.serialize
    assert serialized == {"id":1,"user_id":user.id,"blip_id":blip.id}

  """
  View Tests
  """

  """ User """

  def test_new_user_creates_user_with_valid_data(self):
    rv = self.createUser("ben","testpass","benweitzman@gmail.com")
    assert ast.literal_eval(rv.data) == {"meta": {"status": 20}, "objects": [{"email": "benweitzman@gmail.com", "id": 1, "name": "ben"}]}

  def test_new_user_returns_proper_error_with_bad_data(self):
    rv = self.app.put("/api/user")
    assert ast.literal_eval(rv.data) == {"meta":{"status":10,"error":"Missing Required Parameters"},"objects":[]}

  def test_new_user_email_is_duplicate(self):
    self.generateUser()
    rv = self.createUser("ben2","testpass","benweitzman@gmail.com")
    assert ast.literal_eval(rv.data) == {"meta":{"status":30,"error":"Email already exists"},"objects":[]}

  def test_new_user_username_is_duplicate(self):
    self.generateUser()
    rv = self.createUser("ben","testpass","benweitzman2@gmail.com")
    assert ast.literal_eval(rv.data) == {"meta":{"status":31,"error":"Username already exists"},"objects":[]}

  def test_user_does_authenticate(self):
    self.generateUser()
    rv = self.app.get('/api/user?username=ben&password=testpass')
    assert ast.literal_eval(rv.data) == {"meta":{"status":20},"objects":[{"id":1,"name":"ben","email":"benweitzman@gmail.com"}]}

  def test_user_fails_autentication(self):
    self.generateUser()
    rv = self.app.get('/api/user?username=ben&password=testpa')
    assert ast.literal_eval(rv.data) == {"meta":{"status":32,"error":"Invalid Authentication"},"objects":[]}

    rv = self.app.get('/api/user?username=ben2&password=testpass')
    assert ast.literal_eval(rv.data) == {"meta":{"status":33,"error":"Username does not exist"},"objects":[]}

  """ Song """

  def test_new_song_creates_song_with_valid_data(self):
    rv = self.createSong("The Kinks","Big Sky")
    assert ast.literal_eval(rv.data) == {"meta": {"status": 20},
                                         "objects": [{"id":1,"artist":"The Kinks","title":"Big Sky","album":"","provider_key":"Youtube","provider_song_id":"wiyrFSSG5_g"}]}

  def test_new_song_creates_song_with_invalid_data(self):
    rv = self.app.put("/api/song",data=dict(
      username  = "The Kinks",
      password  = "Big Sky"
    ))
    assert ast.literal_eval(rv.data) == {"meta": {"status": 10, "error": "Missing Required Parameters"}, "objects": []}

  """ Blip """

  def test_new_blip_creates_blip_with_valid_data(self):
    user_dict = self.generateUser()
    song_dict = self.generateSong()
    rv = self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")

    now = datetime.now().isoformat()
    rv_dict = ast.literal_eval(rv.data)
    rv_dict['objects'][0]['timestamp'] = now
    assert rv_dict == {"meta"   : {"status"     : 20}, 
                       "objects":
                                  [{"id"        : 1,
                                    "song"      : song_dict,
                                    "user_id"   : user_dict['id'],
                                    "longitude" : 50.0,
                                    "latitude"  : 50.0,
                                    "timestamp" : now}]}

  def test_new_blip_creates_blip_with_invalid_data(self):
    rv = self.app.put("/api/blip",data=dict(
      latitude  = "50.0",
      password  = "testpass"
    ))

    assert ast.literal_eval(rv.data) == {"meta": {"status": 10, "error": "Missing Required Parameters"}, "objects": []}

  def test_new_blip_creates_blip_with_nonexistant_song_id(self):
    user_dict = self.generateUser()

    # missing parameters
    rv = self.createBlip("50.0","50.0",123,user_dict['id'],"testpass")

    assert ast.literal_eval(rv.data) == {"meta": {"status": 40, "error": "Song ID does not exist"}, "objects": []}

  def test_new_blip_creates_blip_with_nonexistant_user_id(self):
    song_dict = self.generateSong()

    # missing parameters
    rv = self.createBlip("50.0","50.0",song_dict['id'],1234,"testpass")

    assert ast.literal_eval(rv.data) == {"meta": {"status":32, "error": "Invalid Authentication"}, "objects": []}

  def test_new_blip_creates_blip_with_invalid_password(self):
    user_dict = self.generateUser()
    song_dict = self.generateSong()

    # missing parameters
    rv = self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass123")

    assert ast.literal_eval(rv.data) == {"meta": {"status":32, "error": "Invalid Authentication"}, "objects": []}

  def test_get_blip_by_id_with_valid_data(self):
    user_dict = self.generateUser()
    song_dict = self.generateSong()

    self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")

    rv = self.app.get('/api/blip?id=1')
    now = datetime.now().isoformat()
    rv_dict = ast.literal_eval(rv.data)
    rv_dict['objects'][0]['timestamp'] = now
    assert rv_dict == {"meta"   : {"status"    : 20}, 
                       "objects":
                                 [{"id"        : 1,
                                   "song"      : song_dict,
                                   "user_id"   : user_dict['id'],
                                   "longitude" : 50.0,
                                   "latitude"  : 50.0,
                                   "timestamp" : now}]}

  def test_get_nearby_blips_with_valid_data(self):
    user_dict = self.generateUser()
    song_dict = self.generateSong()
    self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")
    self.createBlip("51.0","51.0",song_dict['id'],user_dict['id'],"testpass")

    rv = self.app.get('/api/blip?latitude=50.0&longitude=50.0')
    now = datetime.now().isoformat()
    rv_dict = ast.literal_eval(rv.data)
    rv_dict['objects'][0]['timestamp'] = now
    rv_dict['objects'][1]['timestamp'] = now
    assert rv_dict == {"meta":    {"status":20}, 
                       "objects": [
                                    {"id"        : 1,
                                     "song"      : song_dict,
                                     "user_id"   : user_dict['id'],
                                     "longitude" : 50.0,
                                     "latitude"  : 50.0,
                                     "timestamp" : now},
                                    {"id"        : 2,
                                     "song"      : song_dict,
                                     "user_id"   : user_dict['id'],
                                     "longitude" : 51.0,
                                     "latitude"  : 51.0,
                                     "timestamp" : now}]}

  def test_get_all_blips_with_valid_data(self):
    user_dict = self.generateUser()
    song_dict = self.generateSong()
    self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")
    self.createBlip("51.0","51.0",song_dict['id'],user_dict['id'],"testpass")

    rv = self.app.get('/api/blip')
    now = datetime.now().isoformat()
    rv_dict = ast.literal_eval(rv.data)
    rv_dict['objects'][0]['timestamp'] = now
    rv_dict['objects'][1]['timestamp'] = now
    assert rv_dict == {"meta":    {"status":20}, 
                       "objects": [
                                    {"id"        : 1,
                                     "song"      : song_dict,
                                     "user_id"   : user_dict['id'],
                                     "longitude" : 50.0,
                                     "latitude"  : 50.0,
                                     "timestamp" : now},
                                    {"id"        : 2,
                                     "song"      : song_dict,
                                     "user_id"   : user_dict['id'],
                                     "longitude" : 51.0,
                                     "latitude"  : 51.0,
                                     "timestamp" : now}]}

  """ Comment """

  def test_new_comment_creates_comment_with_valid_data(self):
    user_dict, song_dict, blip_dict = self.generateBlip()
    rv = self.createComment(user_dict['id'],"testpass",blip_dict['id'],"This is a comment")
    now = datetime.now().isoformat()
    rv_dict = ast.literal_eval(rv.data)
    rv_dict['objects'][0]['timestamp'] = now
    assert rv_dict == {"meta": {"status"    : 20}, 
                       "objects":
                              [{"id"        : 1,
                                "blip"      : blip_dict,
                                "user_id"   : user_dict['id'],
                                "comment"   : "This is a comment",
                                "timestamp" : now}]}

  def test_new_comment_create_comment_with_invalid_data(self):
    rv = self.app.put("/api/blip/comment",data=dict(
      blip_id   = 1,
      password  = "testpass"
    ))
    assert ast.literal_eval(rv.data) == {"meta": {"status": 10, "error": "Missing Required Parameters"}, "objects": []}

  def test_new_comment_creates_comment_with_nonexistant_blip_id(self):
    user_dict = self.generateUser()
    rv = self.createComment(user_dict['id'],"testpass",1,"This is a comment")
    assert ast.literal_eval(rv.data) == {"meta": {"status": 50, "error": "Blip ID does not exist"}, "objects": []}

  def test_new_comment_creates_comment_with_nonexistant_user_id(self):
    user_dict, song_dict, blip_dict = self.generateBlip()
    rv = self.createComment(123,"testpass",blip_dict['id'],"This is a comment")
    assert ast.literal_eval(rv.data) == {"meta": {"status": 32, "error": "Invalid Authentication"}, "objects": []}

  def test_new_comment_creates_comment_with_invalid_password(self):
    user_dict, song_dict, blip_dict = self.generateBlip()
    rv = self.createComment(user_dict['id'],"testpass123",blip_dict['id'],"This is a comment")
    assert ast.literal_eval(rv.data) == {"meta": {"status": 32, "error": "Invalid Authentication"}, "objects": []}

  def test_get_comment_by_id_with_valid_data(self):
    user_dict, song_dict, blip_dict,comment_dict = self.generateComment()
    rv = self.app.get('/api/blip/comment?id=1')
    now = datetime.now().isoformat()
    rv_dict = ast.literal_eval(rv.data)
    rv_dict['objects'][0]['timestamp'] = now
    assert rv_dict == {"meta": {"status"    : 20}, 
                       "objects":
                              [{"id"        : 1,
                                "blip"      : blip_dict,
                                "user_id"   : user_dict['id'],
                                "comment"   : "This is a comment",
                                "timestamp" : now}]}

  def test_get_comment_by_blip_id_with_valid_data(self):
    song_dict = self.generateSong()
    user_dict = self.generateUser()
    blip = self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")
    blip_dict = ast.literal_eval(blip.data)['objects'][0]
    blip2 = self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")
    blip2_dict = ast.literal_eval(blip2.data)['objects'][0]
    comment1 = self.createComment(user_dict['id'],"testpass",blip_dict['id'],"This is a comment")
    comment1_dict = ast.literal_eval(comment1.data)['objects'][0]
    comment2 = self.createComment(user_dict['id'],"testpass",blip_dict['id'],"This is a comment part 2")
    comment2_dict = ast.literal_eval(comment2.data)['objects'][0]
    comment3 = self.createComment(user_dict['id'],"testpass",blip2_dict['id'],"This is a comment part 2")
    comment3_dict = ast.literal_eval(comment3.data)['objects'][0]

    rv = self.app.get('/api/blip/comment?blip_id={0}'.format(blip_dict['id']))
    assert ast.literal_eval(rv.data) == {"meta"   : {"status":20}, 
                                         "objects": [comment2_dict,comment1_dict]}

  def test_get_comment_with_invalid_data(self):
    rv = self.app.get('/api/blip/comment')
    assert ast.literal_eval(rv.data) == {"meta":{"status":10,"error":"Missing Required Parameters"},"objects":[]}

  def test_get_comment_with_invalid_id(self):
    rv = self.app.get('/api/blip/comment?id=1')
    assert ast.literal_eval(rv.data) == {"meta":{"status":60,"error":"Comment ID does not exist"},"objects":[]}

  """ Favorites """

  def test_new_favorite_creates_favorite_with_valid_data(self):
    user_dict, song_dict, blip_dict = self.generateBlip()
    rv = self.createFavorite(user_dict['id'],"testpass",blip_dict['id'])
    rv_dict = ast.literal_eval(rv.data)
    assert rv_dict == {"meta": {"status"              : 20}, 
                                "objects":
                                          [{"id"      : 1,
                                            "blip_id" : blip_dict['id'],
                                            "user_id" : user_dict['id']
                                          }]}

  def test_new_favorite_create_favorite_with_invalid_data(self):
    rv = self.app.put("/api/blip/favorite",data=dict(
        username = "tbow"
      ))
    assert ast.literal_eval(rv.data) == {"meta":{"status":10,"error":"Missing Required Parameters"},"objects":[]}

  def test_new_favorite_creates_favorite_with_nonexistant_blip_id(self):
    user_dict = self.generateUser()
    rv = self.createFavorite(1,"testpass",1)
    assert ast.literal_eval(rv.data) == {"meta": {"status": 50, "error": "Blip ID does not exist"}, "objects": []}

  def test_new_favorite_creates_favorite_with_nonexistant_user_id(self):
    user_dict, song_dict, blip_dict = self.generateBlip()
    rv = self.createFavorite(2,"testpass",1)
    assert ast.literal_eval(rv.data) == {"meta": {"status": 32, "error": "Invalid Authentication"}, "objects": []}

  def test_new_favorite_creates_favorite_with_invalid_password(self):
    user_dict, song_dict, blip_dict = self.generateBlip()
    rv = self.createFavorite(1,"testpass123",1)
    assert ast.literal_eval(rv.data) == {"meta": {"status": 32, "error": "Invalid Authentication"}, "objects": []}

  def test_get_favorites_for_blip_with_no_favorties(self):
    user_dict, song_dict, blip_dict = self.generateBlip()
    rv = self.app.get("/api/blip/favorite?blip_id=1")
    rv_dict = ast.literal_eval(rv.data)
    assert rv_dict == {"meta": {"status": 20},
                       "objects":[]}

  def test_get_favorites_for_user_with_no_favorites(self):
    user_dict, song_dict, blip_dict = self.generateBlip()
    rv = self.app.get("/api/blip/favorite?user_id=1")
    rv_dict = ast.literal_eval(rv.data)
    assert rv_dict == {"meta": {"status": 20},
                       "objects":[]}

  def test_get_favorites_for_blips(self):
    user_dict, song_dict, blip_dict = self.generateBlip()
    blip_dict2 = self.createBlip(50,50,1,1,"testpass")
    user_dict2 = self.generateUser(username="ben2",email="ben2@gmail.com")
    user_dict3 = self.generateUser(username="ben3",email="ben3@gmail.com")
    self.createFavorite(1,"testpass",1)
    self.createFavorite(2,"testpass",1)
    self.createFavorite(3,"testpass",2)
    rv = self.app.get("/api/blip/favorite?blip_id=1")
    assert ast.literal_eval(rv.data) == {"meta":{"status":20},
                                         "objects":[user_dict2,user_dict]}

  def test_get_favorites_for_user(self):
    user_dict, song_dict, blip_dict = self.generateBlip()
    blip_dict2 = ast.literal_eval(self.createBlip(50,50,1,1,"testpass").data)['objects'][0]
    user_dict2 = self.generateUser(username="ben2",email="ben2@gmail.com")
    user_dict3 = self.generateUser(username="ben3",email="ben3@gmail.com")
    self.createFavorite(1,"testpass",1)
    self.createFavorite(2,"testpass",1)
    self.createFavorite(3,"testpass",2)
    self.createFavorite(1,"testpass",2)
    rv = self.app.get("/api/blip/favorite?user_id=1")
    assert ast.literal_eval(rv.data) == {"meta":{"status":20},
                                         "objects":[blip_dict,blip_dict2]}

  def test_refavorite_does_nothing(self):
    user_dict, song_dict, blip_dict = self.generateBlip()
    self.createFavorite(1,"testpass",1)
    self.createFavorite(1,"testpass",1)
    rv = self.app.get("/api/blip/favorite?user_id=1")
    rv_dict = ast.literal_eval(rv.data)
    assert rv_dict == {"meta": {"status":20},
                       "objects":[blip_dict]}

  def test_delete_favorite_with_valid_data(self):
    user_dict, song_dict, blip_dict = self.generateBlip()
    self.createFavorite(1,"testpass",1)
    rv = self.app.delete("/api/blip/favorite?user_id=1&blip_id=1&password=testpass")
    assert ast.literal_eval(rv.data) == {"meta":{"status":20},
                                         "objects":[]}
    rv = self.app.get("/api/blip/favorite?user_id=1")
    assert ast.literal_eval(rv.data) == {"meta":{"status":20},
                                         "objects":[]}

  def test_delete_favorite_with_invalid_data(self):
    rv = self.app.delete("/api/blip/favorite")
    assert ast.literal_eval(rv.data) == {"meta":{"status":10,"error":"Missing Required Parameters"},"objects":[]}

  def test_delete_favorite_with_nonexistent_favorite(self):
    user_dict = self.generateUser()
    rv = self.app.delete("/api/blip/favorite?user_id=1&blip_id=1&password=testpass")
    assert ast.literal_eval(rv.data) == {"meta":{"status":70,"error":"Favorite ID does not exist"},"objects":[]}

  def test_delete_favorite_with_invalid_authentication(self):
    user_dict, song_dict, blip_dict = self.generateBlip()
    self.createFavorite(1,"testpass",1)
    rv = self.app.delete("/api/blip/favorite?user_id=1&blip_id=1&password=testpass123")
    assert ast.literal_eval(rv.data) == {"meta": {"status": 32, "error": "Invalid Authentication"}, "objects": []}


if __name__ == '__main__':
  unittest.main()
