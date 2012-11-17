import os
import latitune
import unittest
import tempfile
from datetime import datetime
import ast

class latituneTestCase(unittest.TestCase):

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

  """
  Views
  """

  def test_new_user_creates_user_with_valid_data(self):
    rv = self.app.put("/api/user",data=dict(
      username="ben",
      password="testpass",
      email="benweitzman@gmail.com"
    ))
    assert ast.literal_eval(rv.data) == {"meta": {"status": "OK", "error": ""}, "objects": [{"email": "benweitzman@gmail.com", "id": 1, "name": "ben"}]}

  def test_new_user_returns_proper_error_with_bad_data(self):
    rv = self.app.put("/api/user")
    assert ast.literal_eval(rv.data) == {"meta":{"status":"ERR","error":"Missing required parameters"},"objects":[]}

  def test_new_user_is_duplicate(self):
    rv = self.app.put("/api/user",data=dict(
      username="ben",
      password="testpass",
      email="benweitzman@gmail.com"
    ))
    rv = self.app.put("/api/user",data=dict(
      username="ben",
      password="testpass",
      email="benweitzman@gmail.com"
    ))
    assert ast.literal_eval(rv.data) == {"meta":{"status":"ERR","error":"Username or email already exists"},"objects":[]}

  def test_user_does_authenticate(self):
    self.app.put("/api/user",data=dict(
      username="ben",
      password="testpass",
      email="benweitzman@gmail.com"
    ))
    rv = self.app.get('/api/user?username=ben&password=testpass')
    assert ast.literal_eval(rv.data) == {"meta":{"status":"OK","error":""},"objects":[{"id":1,"name":"ben","email":"benweitzman@gmail.com"}]}

  def test_user_fails_autentication(self):
    self.app.put("/api/user",data=dict(
      username="ben",
      password="testpass",
      email="benweitzman@gmail.com"
    ))
    rv = self.app.get('/api/user?username=ben&password=testpa')
    assert ast.literal_eval(rv.data) == {"meta":{"status":"ERR","error":"Invalid Authentication"},"objects":[]}

    rv = self.app.get('/api/user?username=ben2&password=testpass')
    assert ast.literal_eval(rv.data) == {"meta":{"status":"ERR","error":"Invalid Authentication"},"objects":[]}

  def test_new_song_creates_song_with_valid_data(self):
    rv = self.app.put("/api/song",data=dict(
      artist = "The Kinks",
      title  = "Big Sky"
    ))
    assert ast.literal_eval(rv.data) == {"meta": {"status": "OK", "error": ""},
                                         "objects": [{"id":1,"artist":"The Kinks","title":"Big Sky","album":"","provider_key":"Youtube","provider_song_id":"wiyrFSSG5_g"}]}

  def test_new_song_creates_song_with_invalid_data(self):
    rv = self.app.put("/api/song",data=dict(
      username  = "The Kinks",
      password  = "Big Sky"
    ))
    assert ast.literal_eval(rv.data) == {"meta": {"status": "ERR", "error": "Missing Required Parameters"}, "objects": []}

  def test_new_blip_creates_blip_with_valid_data(self):
    song = self.app.put("/api/song",data=dict(
                  artist = "The Kinks",
                  title  = "Big Sky"
                ))
    song_dict = ast.literal_eval(song.data)['objects'][0]

    user = self.app.put("/api/user",data=dict(
                  username="ben",
                  password="testpass",
                  email="benweitzman@gmail.com"
                ))
    user_dict = ast.literal_eval(user.data)['objects'][0]

    rv = self.app.put("/api/blip",data=dict(
      song_id   = song_dict['id'],
      longitude = "50.0",
      latitude  = "50.0",
      user_id   = user_dict['id'],
      password  = "testpass"
    ))
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

    user = self.app.put("/api/user",data=dict(
                  username="ben",
                  password="testpass",
                  email="benweitzman@gmail.com"
                ))
    user_dict = ast.literal_eval(user.data)['objects'][0]

    # missing parameters
    rv = self.app.put("/api/blip",data=dict(
      song_id   = 123,
      latitude  = "50.0",
      longitude = "50.0",
      user_id   = user_dict['id'],
      password  = "testpass"
    ))


    assert ast.literal_eval(rv.data) == {"meta": {"status": "ERR", "error": "Song ID does not exist"}, "objects": []}

  def test_new_blip_creates_blip_with_nonexistant_user_id(self):
    song = self.app.put("/api/song",data=dict(
                  artist = "The Kinks",
                  title  = "Big Sky"
                ))
    song_dict = ast.literal_eval(song.data)['objects'][0]

    # missing parameters
    rv = self.app.put("/api/blip",data=dict(
      song_id   = song_dict['id'],
      latitude  = "50.0",
      longitude = "50.0",
      user_id   = 1234,
      password  = "testpass"
    ))

    assert ast.literal_eval(rv.data) == {"meta": {"status": "ERR", "error": "User ID does not exist"}, "objects": []}

  def test_new_blip_creates_blip_with_invalid_password(self):
    song = self.app.put("/api/song",data=dict(
                  artist = "The Kinks",
                  title  = "Big Sky"
                ))
    song_dict = ast.literal_eval(song.data)['objects'][0]

    user = self.app.put("/api/user",data=dict(
                  username="ben",
                  password="testpass",
                  email="benweitzman@gmail.com"
                ))
    user_dict = ast.literal_eval(user.data)['objects'][0]

    # missing parameters
    rv = self.app.put("/api/blip",data=dict(
      song_id   = song_dict['id'],
      latitude  = "50.0",
      longitude = "50.0",
      user_id   = user_dict['id'],
      password  = "testpass123"
    ))


    assert ast.literal_eval(rv.data) == {"meta": {"status": "ERR", "error": "Invalid Authentication"}, "objects": []}

  def test_get_blip_by_id_with_valid_data(self):
    song = self.app.put("/api/song",data=dict(
                  artist = "The Kinks",
                  title  = "Big Sky"
                ))
    song_dict = ast.literal_eval(song.data)['objects'][0]

    user = self.app.put("/api/user",data=dict(
                  username="ben",
                  password="testpass",
                  email="benweitzman@gmail.com"
                ))
    user_dict = ast.literal_eval(user.data)['objects'][0]

    self.app.put("/api/blip",data=dict(
      song_id   = song_dict['id'],
      longitude = "50.0",
      latitude  = "50.0",
      user_id   = user_dict['id'],
      password  = "testpass"
    ))

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
    song = self.app.put("/api/song",data=dict(
                  artist = "The Kinks",
                  title  = "Big Sky"
                ))
    song_dict = ast.literal_eval(song.data)['objects'][0]

    user = self.app.put("/api/user",data=dict(
                  username="ben",
                  password="testpass",
                  email="benweitzman@gmail.com"
                ))
    user_dict = ast.literal_eval(user.data)['objects'][0]

    self.app.put("/api/blip",data=dict(
      song_id   = song_dict['id'],
      longitude = "50.0",
      latitude  = "50.0",
      user_id   = user_dict['id'],
      password  = "testpass"
    ))

    self.app.put("/api/blip",data=dict(
      song_id   = song_dict['id'],
      longitude = "51.0",
      latitude  = "51.0",
      user_id   = user_dict['id'],
      password  = "testpass"
    ))

    rv = self.app.get('/api/blip?latitude=50.0&longitude=50.0')
    print(rv.data)
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
    song = self.app.put("/api/song",data=dict(
                  artist = "The Kinks",
                  title  = "Big Sky"
                ))
    song_dict = ast.literal_eval(song.data)['objects'][0]

    user = self.app.put("/api/user",data=dict(
                  username="ben",
                  password="testpass",
                  email="benweitzman@gmail.com"
                ))
    user_dict = ast.literal_eval(user.data)['objects'][0]

    self.app.put("/api/blip",data=dict(
      song_id   = song_dict['id'],
      longitude = "50.0",
      latitude  = "50.0",
      user_id   = user_dict['id'],
      password  = "testpass"
    ))

    self.app.put("/api/blip",data=dict(
      song_id   = song_dict['id'],
      longitude = "51.0",
      latitude  = "51.0",
      user_id   = user_dict['id'],
      password  = "testpass"
    ))

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

if __name__ == '__main__':
  unittest.main()
