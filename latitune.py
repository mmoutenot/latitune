import os
from flask import Flask
from flask_heroku import Heroku
from flask.ext.sqlalchemy import SQLAlchemy

app    = Flask (__name__)
heroku = Heroku (app)
db     = SQLAlchemy (app)

@app.route("/")
def index():
  return "Hello Latitune!"

if __name__ == "__main__":
  # Bind to PORT if defined, otherwise default to 5000.
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port)

