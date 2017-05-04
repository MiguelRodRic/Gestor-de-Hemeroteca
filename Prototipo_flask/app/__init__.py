from flask import Flask
from flask.ext.pymongo import PyMongo

app = Flask(__name__)
app.config.from_object('config')

from app import views