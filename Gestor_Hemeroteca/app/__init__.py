# -*- coding: utf-8 -*-
from flask import Flask
from flask_pymongo import PyMongo
from flask_bootstrap import Bootstrap
from flask_breadcrumbs import Breadcrumbs, register_breadcrumb

app = Flask(__name__)
app.config.from_object('config')
Breadcrumbs(app=app)
Bootstrap(app)

from app import views