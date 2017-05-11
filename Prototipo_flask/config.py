# -*- coding: utf-8 -*-
WTF_CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

import sys, os

class ConfigVars():
	path = os.getcwd()
	pdfpath = os.path.join(path,'pdf')