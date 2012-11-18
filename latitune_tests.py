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

  def createSong(self,artist,title):
    return self.app.put("/api/song",data=dict(
        artist = artist,
        title  = title,
        ))
  
  def createBlip(self,latitude,longitude,song_id,user_id,password):
    return self.app.put("/api/blip",data=dict(
        song_id   = song_id,
        longitude = longitude,
        latitude  = latitude,
        user_id   = user_id,
        password  = password,
        ))
  def createComment(self,user_id,password,blip_id,comment):
    return self.app.put("/api/comment",data=dict(
        blip_id  = blip_id,
        user_id  = user_id,
        password = password,
        comment  = comment
      ))
    
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
  Models
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

  """
  Views
  """

  def test_new_user_creates_user_with_valid_data(self):
    rv = self.createUser("ben","testpass","benweitzman@gmail.com")
    assert ast.literal_eval(rv.data) == {"meta": {"status": "OK", "error": ""}, "objects": [{"email": "benweitzman@gmail.com", "id": 1, "name": "ben"}]}

  def test_new_user_returns_proper_error_with_bad_data(self):
    rv = self.app.put("/api/user")
    assert ast.literal_eval(rv.data) == {"meta":{"status":"ERR","error":"Missing required parameters"},"objects":[]}

  def test_new_user_is_duplicate(self):
    rv = self.createUser("ben","testpass","benweitzman@gmail.com")
    rv = self.createUser("ben","testpass","benweitzman@gmail.com")
    assert ast.literal_eval(rv.data) == {"meta":{"status":"ERR","error":"Username or email already exists"},"objects":[]}

  def test_user_does_authenticate(self):
    self.createUser("ben","testpass","benweitzman@gmail.com")
    rv = self.app.get('/api/user?username=ben&password=testpass')
    assert ast.literal_eval(rv.data) == {"meta":{"status":"OK","error":""},"objects":[{"id":1,"name":"ben","email":"benweitzman@gmail.com"}]}

  def test_user_fails_autentication(self):
    self.createUser("ben","testpass","benweitzman@gmail.com")
    rv = self.app.get('/api/user?username=ben&password=testpa')
    assert ast.literal_eval(rv.data) == {"meta":{"status":"ERR","error":"Invalid Authentication"},"objects":[]}

    rv = self.app.get('/api/user?username=ben2&password=testpass')
    assert ast.literal_eval(rv.data) == {"meta":{"status":"ERR","error":"Invalid Authentication"},"objects":[]}

  def test_new_song_creates_song_with_valid_data(self):
    rv = self.createSong("The Kinks","Big Sky")
    assert ast.literal_eval(rv.data) == {"meta": {"status": "OK", "error": ""},
                                         "objects": [{"id":1,"artist":"The Kinks","title":"Big Sky","album":"","provider_key":"Youtube","provider_song_id":"wiyrFSSG5_g"}]}

  def test_new_song_creates_song_with_invalid_data(self):
    rv = self.app.put("/api/song",data=dict(
      username  = "The Kinks",
      password  = "Big Sky"
    ))
    assert ast.literal_eval(rv.data) == {"meta": {"status": "ERR", "error": "Missing Required Parameters"}, "objects": []}

  def test_new_blip_creates_blip_with_valid_data(self):
    song = self.createSong("The Kinks","Big Sky")
    song_dict = ast.literal_eval(song.data)['objects'][0]
    user = self.createUser("ben","testpass","benweitzman@gmail.com")
    user_dict = ast.literal_eval(user.data)['objects'][0]

    rv = self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")

    now = datetime.now().isoformat()
    rv_dict = ast.literal_eval(rv.data)
    rv_dict['objects'][0]['timestamp'] = now
    assert rv_dict == {"meta": {"status": "OK", "error":
                                                  ""}, "objects":
                                                  [{"id"      : 1,
                                                    "song"    : song_dict,
                                                  "user_id"   : user_dict['id'],
                                                  "longitude" : 50.0,
                                                  "latitude"  : 50.0,
                                                  "timestamp" : now}]}

  def test_new_blip_creates_blip_with_invalid_data(self):
    rv = self.app.put("/api/blip",data=dict(
      latitude  = "50.0",
      password  = "testpass"
    ))

    assert ast.literal_eval(rv.data) == {"meta": {"status": "ERR", "error": "Missing Required Parameters"}, "objects": []}

  def test_new_blip_creates_blip_with_nonexistant_song_id(self):
    user = self.createUser("ben","testpass","benweitzman@gmail.com")
    user_dict = ast.literal_eval(user.data)['objects'][0]

    # missing parameters
    rv = self.createBlip("50.0","50.0",123,user_dict['id'],"testpass")

    assert ast.literal_eval(rv.data) == {"meta": {"status": "ERR", "error": "Song ID does not exist"}, "objects": []}

  def test_new_blip_creates_blip_with_nonexistant_user_id(self):
    song = self.createSong("The Kinks","Big Sky")
    song_dict = ast.literal_eval(song.data)['objects'][0]

    # missing parameters
    rv = self.createBlip("50.0","50.0",song_dict['id'],1234,"testpass")


    assert ast.literal_eval(rv.data) == {"meta": {"status": "ERR", "error": "User ID does not exist"}, "objects": []}

  def test_new_blip_creates_blip_with_invalid_password(self):
    song = self.createSong("The Kinks","Big Sky")
    song_dict = ast.literal_eval(song.data)['objects'][0]
    user = self.createUser("ben","testpass","benweitzman@gmail.com")
    user_dict = ast.literal_eval(user.data)['objects'][0]

    # missing parameters
    rv = self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass123")

    assert ast.literal_eval(rv.data) == {"meta": {"status": "ERR", "error": "Invalid Authentication"}, "objects": []}

  def test_get_blip_by_id_with_valid_data(self):
    song = self.createSong("The Kinks","Big Sky")
    song_dict = ast.literal_eval(song.data)['objects'][0]
    user = self.createUser("ben","testpass","benweitzman@gmail.com")
    user_dict = ast.literal_eval(user.data)['objects'][0]

    self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")

    rv = self.app.get('/api/blip?id=1')
    now = datetime.now().isoformat()
    rv_dict = ast.literal_eval(rv.data)
    rv_dict['objects'][0]['timestamp'] = now
    assert rv_dict == {"meta": {"status": "OK", "error":
                                                  ""}, "objects":
                                                  [{"id"      : 1,
                                                    "song"    : song_dict,
                                                  "user_id"   : user_dict['id'],
                                                  "longitude" : 50.0,
                                                  "latitude"  : 50.0,
                                                  "timestamp" : now}]}
  def test_get_nearby_blips_with_valid_data(self):
    song = self.createSong("The Kinks","Big Sky")
    song_dict = ast.literal_eval(song.data)['objects'][0]
    user = self.createUser("ben","testpass","benweitzman@gmail.com")
    user_dict = ast.literal_eval(user.data)['objects'][0]
    self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")
    self.createBlip("51.0","51.0",song_dict['id'],user_dict['id'],"testpass")

    rv = self.app.get('/api/blip?latitude=50.0&longitude=50.0')
    now = datetime.now().isoformat()
    rv_dict = ast.literal_eval(rv.data)
    rv_dict['objects'][0]['timestamp'] = now
    rv_dict['objects'][1]['timestamp'] = now
    assert rv_dict == {"meta": {"status": "OK", "error":
                                                  ""}, "objects": [
                                                    {"id"      : 1,
                                                    "song"    : song_dict,
                                                  "user_id"   : user_dict['id'],
                                                  "longitude" : 50.0,
                                                  "latitude"  : 50.0,
                                                  "timestamp" : now},
                                                    {"id"      : 2,
                                                    "song"    : song_dict,
                                                  "user_id"   : user_dict['id'],
                                                  "longitude" : 51.0,
                                                  "latitude"  : 51.0,
                                                  "timestamp" : now}]}

  def test_get_all_blips_with_valid_data(self):
    song = self.createSong("The Kinks","Big Sky")
    song_dict = ast.literal_eval(song.data)['objects'][0]
    user = self.createUser("ben","testpass","benweitzman@gmail.com")
    user_dict = ast.literal_eval(user.data)['objects'][0]

    self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")
    self.createBlip("51.0","51.0",song_dict['id'],user_dict['id'],"testpass")

    rv = self.app.get('/api/blip')
    now = datetime.now().isoformat()
    rv_dict = ast.literal_eval(rv.data)
    rv_dict['objects'][0]['timestamp'] = now
    rv_dict['objects'][1]['timestamp'] = now
    assert rv_dict == {"meta": {"status": "OK", "error":
                                                  ""}, "objects": [
                                                    {"id"      : 1,
                                                    "song"    : song_dict,
                                                  "user_id"   : user_dict['id'],
                                                  "longitude" : 50.0,
                                                  "latitude"  : 50.0,
                                                  "timestamp" : now},
                                                    {"id"      : 2,
                                                    "song"    : song_dict,
                                                  "user_id"   : user_dict['id'],
                                                  "longitude" : 51.0,
                                                  "latitude"  : 51.0,
                                                  "timestamp" : now}]}

  def test_new_comment_creates_comment_with_valid_data(self):
    song = self.createSong("The Kinks","Big Sky")
    song_dict = ast.literal_eval(song.data)['objects'][0]
    user = self.createUser("ben","testpass","benweitzman@gmail.com")
    user_dict = ast.literal_eval(user.data)['objects'][0]
    blip = self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")
    blip_dict = ast.literal_eval(blip.data)['objects'][0]

    rv = self.createComment(user_dict['id'],"testpass",blip_dict['id'],"This is a comment")
    now = datetime.now().isoformat()
    rv_dict = ast.literal_eval(rv.data)
    rv_dict['objects'][0]['timestamp'] = now
    assert rv_dict == {"meta": {"status": "OK", "error":
                                                  ""}, "objects":
                                                  [{"id"      : 1,
                                                    "blip"    : blip_dict,
                                                  "user_id"   : user_dict['id'],
                                                  "comment"   : "This is a comment",
                                                  "timestamp" : now}]}

  def test_new_comment_create_comment_with_invalid_data(self):
    rv = self.app.put("/api/comment",data=dict(
      blip_id   = 1,
      password  = "testpass"
    ))
    assert ast.literal_eval(rv.data) == {"meta": {"status": "ERR", "error": "Missing Required Parameters"}, "objects": []}

  def test_new_comment_creates_comment_with_nonexistant_blip_id(self):
    user = self.createUser("ben","testpass","benweitzman@gmail.com")
    user_dict = ast.literal_eval(user.data)['objects'][0]
    rv = self.createComment(user_dict['id'],"testpass",1,"This is a comment")
    assert ast.literal_eval(rv.data) == {"meta": {"status": "ERR", "error": "Blip ID does not exist"}, "objects": []}

  def test_new_blip_creates_blip_with_nonexistant_user_id(self):
    user = self.createUser("ben","testpass","benweitzman@gmail.com")
    user_dict = ast.literal_eval(user.data)['objects'][0]
    song = self.createSong("The Kinks","Big Sky")
    song_dict = ast.literal_eval(song.data)['objects'][0]
    blip = self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")
    blip_dict = ast.literal_eval(blip.data)['objects'][0]
    rv = self.createComment(123,"testpass",blip_dict['id'],"This is a comment")
    assert ast.literal_eval(rv.data) == {"meta": {"status": "ERR", "error": "User ID does not exist"}, "objects": []}

  def test_new_blip_creates_blip_with_invalid_password(self):
    song = self.createSong("The Kinks","Big Sky")
    song_dict = ast.literal_eval(song.data)['objects'][0]
    user = self.createUser("ben","testpass","benweitzman@gmail.com")
    user_dict = ast.literal_eval(user.data)['objects'][0]
    blip = self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")
    blip_dict = ast.literal_eval(blip.data)['objects'][0]
    rv = self.createComment(user_dict['id'],"testpass123",blip_dict['id'],"This is a comment")
    assert ast.literal_eval(rv.data) == {"meta": {"status": "ERR", "error": "Invalid Authentication"}, "objects": []}

  def test_get_comment_by_id_with_valid_data(self):
    song = self.createSong("The Kinks","Big Sky")
    song_dict = ast.literal_eval(song.data)['objects'][0]
    user = self.createUser("ben","testpass","benweitzman@gmail.com")
    user_dict = ast.literal_eval(user.data)['objects'][0]
    blip = self.createBlip("50.0","50.0",song_dict['id'],user_dict['id'],"testpass")
    blip_dict = ast.literal_eval(blip.data)['objects'][0]
    comment = self.createComment(user_dict['id'],"testpass",blip_dict['id'],"This is a comment")
    comment_dict = ast.literal_eval(comment.data)['objects'][0]

    rv = self.app.get('/api/comment?id=1')
    now = datetime.now().isoformat()
    rv_dict = ast.literal_eval(rv.data)
    rv_dict['objects'][0]['timestamp'] = now
    assert rv_dict == {"meta": {"status": "OK", "error":
                                                  ""}, "objects":
                                                  [{"id"      : 1,
                                                    "blip"    : blip_dict,
                                                  "user_id"   : user_dict['id'],
                                                  "comment"   : "This is a comment",
                                                  "timestamp" : now}]}

  def test_get_comment_by_blip_id_with_valid_data(self):
    song = self.createSong("The Kinks","Big Sky")
    song_dict = ast.literal_eval(song.data)['objects'][0]
    user = self.createUser("ben","testpass","benweitzman@gmail.com")
    user_dict = ast.literal_eval(user.data)['objects'][0]
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

    rv = self.app.get('/api/comment?blip_id={0}'.format(blip_dict['id']))
    assert ast.literal_eval(rv.data) == {"meta": {"status": "OK", "error":
                                                  ""}, "objects":
                                                  [comment2_dict,comment1_dict]}

  def test_get_comment_with_invalid_data(self):
    rv = self.app.get('/api/comment')
    assert ast.literal_eval(rv.data) == {"meta":{"status":"ERR","error":"Missing Required Parameters"},"objects":[]}  
      
  def test_get_comment_with_invalid_id(self):
    rv = self.app.get('/api/comment?id=1')
    assert ast.literal_eval(rv.data) == {"meta":{"status":"ERR","error":"Comment ID does not exist"},"objects":[]}  

                                              

if __name__ == '__main__':
  unittest.main()
