# -*- coding: utf-8 -*-
"""Clases usadas en los formularios de la aplicación web"""
from flask_wtf import FlaskForm as Form
from wtforms import StringField
from sklearn.linear_model import LogisticRegression
from nltk.corpus import stopwords
from sklearn import ensemble, feature_extraction
from lime.lime_text import LimeTextExplainer
from sklearn.pipeline import make_pipeline
import pandas as pd
from pymongo import MongoClient
from bson.objectid import ObjectId
import unicodedata

CLIENT = MongoClient()
DB = CLIENT.test_database
NOTICIAS_DB = DB.noticias
DATASETS = DB.datasets

#Most of this function obtained from: http://stackoverflow.com/questions/4119070/how-to-divide-a-list-into-n-equal-parts-python
def split_in_3(list_to_divide):
    """Función para dividir textos en tres partes iguales. Se usó para casos extraordinarios."""
    size = len(list_to_divide)
    slice_size = size / 3
    remain = size % 3
    result = []
    iterator = iter(list_to_divide)
    for i in range(3):
        result.append([])
        for j in range(slice_size):
            result[i].append(iterator.next())
        if remain:
            result[i].append(iterator.next())
            remain -= 1
    return result

def prepare_model(training_data, tag):
    """Prepara el conjunto de entrenamiento para que los usen los clasificadores"""
    trainset = []
    texto_noticias = []
    etiqueta_noticias = []
    result_test = []
    for noticia in training_data:
        texto_encoded = noticia['text'].encode('ASCII', 'ignore')
        texto_noticias.append(texto_encoded.encode('utf-8'))
        etiqueta_noticias.append(noticia['tag'][tag])
    for noticia in texto_noticias:
        index = texto_noticias.index(noticia)
        etiqueta = etiqueta_noticias[index]
        trainset.append((noticia, etiqueta))
    trainset_sk = []
    for couple in trainset:
        trainset_sk.append((couple[0], couple[1]))
    return trainset_sk

class Query(Form):
    """Clase usada en la generación de la tabla de resultados y explicaciones"""
    noticiasSample = []
    search = StringField('')
    def classification(self, noticia_id, tag):
        """Realiza la prediccion de la clase de un texto para un conjunto de datos"""
        palabras_filtrar = stopwords.words('spanish')
        try:
            clases = DATASETS.find_one({'dataset':tag})['clases']
            conjunto_entrenamiento = NOTICIAS_DB.find({'tag.'+tag:{'$exists':True, "$ne":""}})
            target = NOTICIAS_DB.find_one({'_id':ObjectId(noticia_id)})
            trainset = prepare_model(conjunto_entrenamiento, tag)
            labels = ['text', 'opinion']
            tabla = pd.DataFrame.from_records(trainset, columns=labels)
            tabla['opinion_num'] = tabla.opinion.map({clases['clase1']:0, clases['clase2']:1})
            x = tabla.text
            y = tabla.opinion
            labels = []
            for opinion in y:
                if opinion == clases['clase1']:
                    labels.append(0)
                else:
                    labels.append(1)
            vectorizer = feature_extraction.text.TfidfVectorizer(stop_words=palabras_filtrar)
            rf = ensemble.RandomForestClassifier(n_estimators=90)
            train_vectors = vectorizer.fit_transform(x)
            rf.fit(train_vectors, labels)
            c = make_pipeline(vectorizer, rf)
            prediction_both = c.predict_proba([target['text']])
            prediction_for = prediction_both[0, 0]
            prediction_against = prediction_both[0, 1]
            prediction = {'aFavor':prediction_for, 'enContra':prediction_against}
            return prediction
        except Exception as e:
            errorText = str(e)
            return errorText
    def explanation(self, noticia_id, tag):
        """Crea la explicación de una predicción"""
        palabras_filtrar = stopwords.words('spanish')
        clases = DATASETS.find_one({'dataset':tag})['clases']
        conjunto_entrenamiento = NOTICIAS_DB.find({'tag.'+tag:{'$exists':True, "$ne":""}})
        target = NOTICIAS_DB.find_one({'_id':ObjectId(noticia_id)})
        trainset = prepare_model(conjunto_entrenamiento, tag)
        labels = ['text', 'opinion']
        trainset_sk = []
        for couple in trainset:
            trainset_sk.append((couple[0], couple[1]))
        tabla = pd.DataFrame.from_records(trainset_sk, columns=labels)
        tabla['opinion_num'] = tabla.opinion.map({clases['clase1']:0, clases['clase2']:1})
        x = tabla.text
        y = tabla.opinion
        labels = []
        for opinion in y:
            if opinion == clases['clase1']:
                labels.append(0)
            else:
                labels.append(1)
        explainer = LimeTextExplainer(class_names=[clases['clase1'], clases['clase2']])
        vectorizer = feature_extraction.text.TfidfVectorizer(stop_words=palabras_filtrar)
        rf = ensemble.RandomForestClassifier(n_estimators=200)
        train_vectors = vectorizer.fit_transform(x)
        rf.fit(train_vectors, labels)
        c = make_pipeline(vectorizer, rf)
        shown_text = unicodedata.normalize('NFKD', target['text']).encode('ASCII', 'ignore')
        explanation = explainer.explain_instance(shown_text, c.predict_proba, num_features=10)
        result_explanation = {'html':explanation.as_html(), 'list':conjunto_entrenamiento.count()}
        return result_explanation


class Dataset(Form):
    """Clase usada en el formulario de creación de conjuntos de datos"""
    nombredataset = StringField('')
    clase1 = StringField('')
    clase2 = StringField('')

class NewsPDF(Form):
    """Clase usada en el formulario de lectura de PDF"""
    noticias = []

class NewsRSS(Form):
    """Clase usada en el formulario de Web Scraping"""
    media = StringField('')
    noticias = []

class Corpus(Form):
    """Clase usada en el formulario de lectura de corpus enteros"""
    noticias = []
