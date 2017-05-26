# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm as Form
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired
from wtforms import SubmitField
from sklearn.model_selection import train_test_split
from sklearn.model_selection import LeaveOneOut
from sklearn.model_selection import LeavePOut
from sklearn.model_selection import ShuffleSplit
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn import metrics
from sklearn.linear_model import LogisticRegression
from nltk.corpus import stopwords
import lime
from sklearn import ensemble
from sklearn import feature_extraction
from lime.lime_text import LimeTextExplainer
from sklearn.pipeline import make_pipeline
import pandas as pd
import numpy as np
import re
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import sys
from textblob.blob import TextBlob
from textblob.classifiers import NaiveBayesClassifier
from textblob.classifiers import PositiveNaiveBayesClassifier
import nltk 
from bs4 import BeautifulSoup
import urllib2

cliente = MongoClient()
db = cliente.test_database
noticias = db.noticias

#Most of this function obtained from: http://stackoverflow.com/questions/4119070/how-to-divide-a-list-into-n-equal-parts-python
def splitIn3(listToDivide):
	size = len(listToDivide)
	slice_size = size / 3
	remain = size % 3
	result = []
	iterator = iter(listToDivide)
	for i in range(3):
		result.append([])
		for j in range(slice_size):
			result[i].append(iterator.next())
		if remain:
			result[i].append(iterator.next())
			remain -= 1
	return result

class Query(Form):
	noticiasSample = []
	search = StringField('')
	palabras_filtrar = stopwords.words('spanish')
	def classification(args,titulo):
		palabras_filtrar = stopwords.words('spanish')
		conjunto_entrenamiento = noticias.find({'source':{'$regex': "DataSet Isabel"}})
		target =  noticias.find_one({'_id':ObjectId(titulo)})
		trainset = []
		textoNoticias = []
		etiquetaNoticias = []
		result_test = []
		for noticia in conjunto_entrenamiento:
			textoNoticias.append(noticia['text'])
			etiquetaNoticias.append(noticia['tag']['VientreAlquiler'])
		for noticia in textoNoticias:
			index = textoNoticias.index(noticia)
			etiqueta = etiquetaNoticias[index]
			"""noticiablob = TextBlob(noticia)
												result_test.append(noticiablob.sentences)
												for blob in splitIn3(noticia):
													trainset.append((blob, etiqueta))"""
			trainset.append((noticia,etiqueta))
		#nb = MultinomialNB()
		labels = ['text','opinion']
		trainsetSK = []
		
		for sentence in trainset:
			trainsetSK.append((sentence[0],sentence[1]))
		tabla = pd.DataFrame.from_records(trainsetSK, columns=labels)
		tabla['opinion_num'] = tabla.opinion.map({'aFavor':0, 'enContra':1})
		X = tabla.text
		Y = tabla.opinion
		#Split the data to obtain training sentences, training labels, test sentences and test labels
		X_train, X_test, Y_train, Y_test = train_test_split(X, Y, random_state=1)
		#vect = CountVectorizer(stop_words=palabras_filtrar)
		ss = ShuffleSplit(n_splits=1, test_size=0.1, random_state=0)
		X_ShuffleSplit = np.array(trainset)
		ss.get_n_splits(X_ShuffleSplit)
		X_train_counts = []
		X_train_data = []
		X_train_label = []
		X_test_data = []
		X_test_label = []
		trainAux = []
		testAux = []
		for train_index, test_index in ss.split(X_ShuffleSplit):
			trainAux = train_index
			testAux = test_index
		for index in trainAux:
			X_train_data.append(X_ShuffleSplit[index][0])
			if X_ShuffleSplit[index][1] == 'A Favor':
				X_train_label.append(0)
			else:
				X_train_label.append(1)
		for index in testAux:
			X_test_data.append(X_ShuffleSplit[index][0])
			if X_ShuffleSplit[index][1] == 'A Favor':
				X_test_label.append(0)
			else:
				X_test_label.append(1)
		#Training data
		#X_train_counts = vect.fit_transform(X_train_data)
		#tf_transformer = TfidfTransformer(use_idf=False).fit(X_train_counts)
		#X_train_tf = tf_transformer.transform(X_train_counts)
		#X_train_tf.shape
		#nb.fit(X_train_tf, X_train_label)
		#explainer = LimeTextExplainer(class_names=labels)
		vectorizer = feature_extraction.text.TfidfVectorizer(lowercase=False, stop_words=palabras_filtrar)
		rf = ensemble.RandomForestClassifier(n_estimators=100)
		train_vectors = vectorizer.fit_transform(X_train_data)
		#test_vectors = vectorizer.transform(X_test_data)
		rf.fit(train_vectors, X_train_label)
		#pred = rf.predict(test_vectors)
		c = make_pipeline(vectorizer, rf)
		prediction_both = c.predict_proba([target['text']])
		prediction_for = prediction_both[0,0]
		prediction_against = prediction_both[0,1]
		prediction = {'aFavor':prediction_for, 'enContra':prediction_against}
		#explanation = explainer.explain_instance(target['text'], c.predict_proba, num_features=8)
		#result = { 'prediction': prediction, 'explanation': explanation.as_list()}
		return prediction

	def explanation(args, titulo):
		palabras_filtrar = stopwords.words('spanish')
		conjunto_entrenamiento = noticias.find({'source':{'$regex': "DataSet Isabel"}})
		target =  noticias.find_one({'_id':ObjectId(titulo)})
		trainset = []
		textoNoticias = []
		etiquetaNoticias = []
		result_test = []
		for noticia in conjunto_entrenamiento:
			textoNoticias.append(noticia['text'])
			etiquetaNoticias.append(noticia['tag']['VientreAlquiler'])
		for noticia in textoNoticias:
			index = textoNoticias.index(noticia)
			etiqueta = etiquetaNoticias[index]
			trainset.append((noticia,etiqueta))
		#nb = MultinomialNB()
		labels = ['text','opinion']
		trainsetSK = []
		
		for sentence in trainset:
			trainsetSK.append((sentence[0],sentence[1]))
		tabla = pd.DataFrame.from_records(trainsetSK, columns=labels)
		tabla['opinion_num'] = tabla.opinion.map({'aFavor':0, 'enContra':1})
		X = tabla.text
		Y = tabla.opinion
		#Split the data to obtain training sentences, training labels, test sentences and test labels
		X_train, X_test, Y_train, Y_test = train_test_split(X, Y, random_state=1)
		#vect = CountVectorizer(stop_words=palabras_filtrar)
		ss = ShuffleSplit(n_splits=1, test_size=0.1, random_state=0)
		X_ShuffleSplit = np.array(trainset)
		ss.get_n_splits(X_ShuffleSplit)
		X_train_counts = []
		X_train_data = []
		X_train_label = []
		X_test_data = []
		X_test_label = []
		trainAux = []
		testAux = []
		for train_index, test_index in ss.split(X_ShuffleSplit):
			trainAux = train_index
			testAux = test_index
		for index in trainAux:
			X_train_data.append(X_ShuffleSplit[index][0])
			if X_ShuffleSplit[index][1] == 'A Favor':
				X_train_label.append(0)
			else:
				X_train_label.append(1)
		for index in testAux:
			X_test_data.append(X_ShuffleSplit[index][0])
			if X_ShuffleSplit[index][1] == 'A Favor':
				X_test_label.append(0)
			else:
				X_test_label.append(1)
		explainer = LimeTextExplainer(class_names=["A Favor","En Contra"])
		vectorizer = feature_extraction.text.TfidfVectorizer(lowercase=False, stop_words=palabras_filtrar)
		rf = ensemble.RandomForestClassifier(n_estimators=100)
		train_vectors = vectorizer.fit_transform(X_train_data)
		#test_vectors = vectorizer.transform(X_test_data)
		rf.fit(train_vectors, X_train_label)
		#pred = rf.predict(test_vectors)
		c = make_pipeline(vectorizer, rf)
		explanation = explainer.explain_instance(target['text'], c.predict_proba, num_features=10)
		result_explanation = {'html':explanation.as_html(), 'list':explanation.as_list()}

		return result_explanation



class LoginForm(Form):
	openid = StringField('openid', validators=[DataRequired()])
	remember_me = BooleanField('remember_me', default=False)

class ScanPDF(Form):
	noticias=[]

class RssScrapping(Form):
	media = StringField('')
	noticias = []

class NewDataSet(Form):
	noticias = []