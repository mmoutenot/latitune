import os
import latitune
import unittest
import tempfile

class latituneTestCase(unittest.TestCase):

    def setUp(self):
        latitune.db.create_all()

    def tearDown(self):
    	latitune.db.session.remove()
    	latitune.db.drop_all()

    def test_db_sets_up(self):
        user = latitune.User("ben","benweitzman@gmail.com","testpass")
        latitune.db.session.add(user)
        latitune.db.session.commit()
        assert (latitune.User.query.first().name == "ben")

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


if __name__ == '__main__':
    unittest.main()
