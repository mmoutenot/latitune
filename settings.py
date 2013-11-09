##################################################
# SETTINGS AND CONFIG
##################################################

import os
import sys
from flask import Flask
from flask_heroku import Heroku
from flask.ext.sqlalchemy import SQLAlchemy
import gdata.youtube
import gdata.youtube.service
from pyechonest import config

yt_service = gdata.youtube.service.YouTubeService()
yt_service.developer_key = 'AI39si4fdpqYBz4_a6E7choIqT5hIlYhbI4Ucp5eiXGDt5jzE46XM_KxWn5KtwdrAZp6WeMF9Jrzk-sXabs0R_F9T9MHZdiOYA'

echonest_api_key = "DUQVSZTKUIUQIMZXI"

echonest_consumer_key = "a153717c2cadf7b95fe9b8b245faa32d"

echonest_shared_secret = "ILLKK9HORVm37YkaFfTP3w"

rdio_api_key = "xya6sc2u4x73sgvsdtc8ef4k"
rdio_shared_secret = "hs68psbjtH"

config.ECHO_NEST_API_KEY=echonest_api_key


app       = Flask (__name__)
if os.environ.get('LATITUNE_LOCAL') == "true":
  print 'running in developer mode for latitune'
  app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/latitune_dev'
else:
  heroku    = Heroku(app)
app.debug = True

db        = SQLAlchemy (app)
