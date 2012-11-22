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

yt_service = gdata.youtube.service.YouTubeService()
yt_service.developer_key = 'AI39si4fdpqYBz4_a6E7choIqT5hIlYhbI4Ucp5eiXGDt5jzE46XM_KxWn5KtwdrAZp6WeMF9Jrzk-sXabs0R_F9T9MHZdiOYA'

app       = Flask (__name__)
if os.environ.get('LATITUNE_LOCAL') == "true":
  print 'running in developer mode for latitune'
  app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/latitune_dev'
else:
  heroku    = Heroku(app)
app.debug = True

db        = SQLAlchemy (app)
