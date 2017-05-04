# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import re
from IPython.display import display
from IPython.display import clear_output
from IPython.display import HTML
from ipywidgets import widgets
import pymongo
from pymongo import MongoClient
import matplotlib
import matplotlib.pyplot as plt
import sys
from textblob.blob import TextBlob
from textblob.classifiers import NaiveBayesClassifier
from textblob.classifiers import PositiveNaiveBayesClassifier
import nltk 
from bs4 import BeautifulSoup
import urllib2

#nltk.download()

cliente = MongoClient()
db = cliente.test_database
noticias = db.noticias



linksAgainst = ['https://judithbosch.wordpress.com/2017/03/25/mi-vientre-no-se-alquila/', 
           'http://www.tribunafeminista.org/2017/02/dones-juristes-senala-los-intereses-de-lobbies-economicos-en-el-debate-del-alquiler-de-vientres/',
           'http://www.tribunafeminista.org/2017/01/una-nueva-clausula-del-contrato-sexual-vientres-de-alquiler/',
           'http://www.paralelo36andalucia.com/los-vientres-de-alquiler-la-cara-mas-brutal-del-gaypitalismo/',
           'http://www.tribunafeminista.org/2017/02/explotacion-reproductiva/',
           'https://beatrizgimeno.es/2017/03/18/vientres-de-alquiler-y-aborto/',
           'http://www.elmundo.es/baleares/2017/02/03/5894548446163f836a8b4655.html',
           'http://elpais.com/elpais/2016/05/06/tentaciones/1462535192_740903.html',
           'http://elpais.com/elpais/2017/03/01/opinion/1488376776_471436.html',
           'http://elpais.com/elpais/2017/02/13/opinion/1487011358_053416.html',
           'http://elpais.com/elpais/2015/07/27/eps/1438008645_417941.html',
           'http://elpais.com/elpais/2017/02/01/opinion/1485969099_452388.html']
linksFor = ['http://www.elmundo.es/opinion/2017/02/11/589dfd6a468aeb24118b4616.html',
           'http://www.deia.com/2016/10/09/sociedad/euskadi/mucho-mas-que-un-vientre',
           'http://sociedad.elpais.com/sociedad/2014/05/01/actualidad/1398974404_290772.html',
           'http://internacional.elpais.com/internacional/2017/02/22/mexico/1487799528_068485.html',
           'http://elpais.com/elpais/2014/07/06/opinion/1404657061_919858.html',
           'http://elpais.com/elpais/2017/02/25/opinion/1488039785_039670.html',
           'http://internacional.elpais.com/internacional/2014/11/03/actualidad/1414999655_905774.html',
           'http://politica.elpais.com/politica/2017/02/06/actualidad/1486383023_272932.html',
           'http://elpais.com/elpais/2017/03/01/opinion/1488395907_827633.html',
           'http://ccaa.elpais.com/ccaa/2015/12/29/valencia/1451385119_992970.html',
           'http://elpais.com/elpais/2017/02/17/videos/1487339232_876585.html',
           'http://www.elmundo.es/sociedad/2017/03/05/58bbe43cca4741c1428b4579.html']

hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

def filtroTexto(element):
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match('<!--.-->', str(element)):
        return False
    else:
        return True

#Almacenamiento de las frases en contra
noticiasAgainst = [None]*len(linksAgainst)
for linkA in linksAgainst:
    request = urllib2.Request(linkA, headers=hdr)
    handle = urllib2.urlopen(request)
    content = handle.read()
    soup = BeautifulSoup(content, 'html.parser')
    for expendable in soup(['style', 'script', '[document]', 'head', 'title']):
        expendable.extract()
    noticiasAgainst[linksAgainst.index(linkA)] = soup.getText()

textsAgainst = [None]*len(noticiasAgainst)
textSentencesAgainst = [None]*len(noticiasAgainst)

for noticia in noticiasAgainst:
    index = noticiasAgainst.index(noticia)
    textsAgainst[index] = TextBlob(noticiasAgainst[index])   
    sentencesAux = []
    for sentence in textsAgainst[index].sentences:
        sentencesAux.append((sentence,'enContra'))
    textSentencesAgainst[index] = sentencesAux


#Almacenamiento de las frases a favor
noticiasFor = [None]*len(linksFor)
for linkF in linksFor:
    request = urllib2.Request(linkF, headers=hdr)
    handle = urllib2.urlopen(request)
    content = handle.read()
    soup = BeautifulSoup(content, 'html.parser')
    for expendable in soup(['style', 'script', '[document]', 'head', 'title']):
        expendable.extract()
    noticiasFor[linksFor.index(linkF)] = soup.getText()

textsFor = [None]*len(noticiasFor)
textSentencesFor = [None]*len(noticiasFor)

for noticia in noticiasFor:
    index = noticiasFor.index(noticia)
    textsFor[index] = TextBlob(noticiasFor[index])
    sentencesAux = []
    for sentence in textsFor[index].sentences:
        sentencesAux.append((sentence,'aFavor'))
    textSentencesFor[index] = sentencesAux
print 'ok'

trainset = []
#Nos vamos a quedar solo con 300 sentencias de cada tipo
#Con los ejemplos dados, hay muchas mas sentencias en contra que a favor
#lo cual puede empujar al clasificador a clasificar todo como en contra
contadorAgainst = 0
contadorFor = 0
limite = 300 
limiteCross = 350
paraY1Out = []

#Cogemos otro conjunto para las validaciones cruzadas de sklearn

for sentences in textSentencesFor:
    for sentence in sentences:
        if contadorFor < limite:
            trainset.append(sentence)
            contadorFor += 1
        elif contadorFor < limiteCross:
            paraY1Out.append(sentence)
            contadorFor += 1
for sentences in textSentencesAgainst:
    for sentence in sentences:
        if contadorAgainst < limite:
            trainset.append(sentence)
            contadorAgainst += 1
        elif contadorAgainst < limiteCross:
            paraY1Out.append(sentence)
            contadorAgainst += 1

classifier = NaiveBayesClassifier(trainset)

classifier.classify('la gestación subrogada es una práctica de reproducción que se realiza desde hace más de treinta años.') +":" +str(round(classifier.prob_classify('En Estados Unidos, la gestación subrogada es una práctica de reproducción que se realiza desde hace más de treinta años.').prob("aFavor"), 2))
for sentence in trainset:
    if round(classifier.prob_classify(sentence[0]).prob("enContra"), 2) > 0:
        print sentence[0] + "\n" +  classifier.classify(sentence[0]) + str(round(classifier.prob_classify(sentence[0]).prob("enContra"), 2))

#PARTE SCIKIT 

from sklearn.model_selection import train_test_split
from sklearn.model_selection import LeaveOneOut
from sklearn.model_selection import LeavePOut
from sklearn.model_selection import ShuffleSplit
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn import metrics
from sklearn.linear_model import LogisticRegression

loo = LeaveOneOut()


nb = MultinomialNB()
labels = ['text','opinion']
import pandas as pd 
trainsetSK = []
for sentence in trainset:
    trainsetSK.append((str(sentence[0]).decode("utf-8"),sentence[1]))

tabla = pd.DataFrame.from_records(trainsetSK, columns=labels)

tabla['opinion_num'] = tabla.opinion.map({'aFavor':0, 'enContra':1})
X = tabla.text
Y = tabla.opinion

#Split the data to obtain training sentences, training labels, test sentences and test labels
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, random_state=1)

vect = CountVectorizer()

#Learns the training data and creates a document-term matrix from it in one step
X_train_dtm = vect.fit_transform(X_train)

#Same thing with the testing data
X_test_dtm = vect.transform(X_test)

#Naive Bayes is much faster than other alternatives
nb.fit(X_train_dtm, Y_train)

#Make class predictions from X_test_dtm
Y_pred_class = nb.predict(X_test_dtm)
"""
print(metrics.accuracy_score(Y_test, Y_pred_class))
#Confusion matrix
print(metrics.confusion_matrix(Y_test, Y_pred_class))
#print false positives
print(X_test[(Y_pred_class==1) & (Y_test==0)])
"""

logreg = LogisticRegression()

#Prepares training data, for labels and messages
logreg.fit(X_train_dtm, Y_train)

#Make class predictions for X_test_dtm
Y_pred_class = logreg.predict(X_test_dtm)

#Calculate predicted probabilities for X_test_dtm
y_pred_prob = logreg.predict_proba(X_test_dtm)[:,1]

X_train_tokens = vect.get_feature_names()


#Count the number of appereances of each token
"""
print(nb.feature_count_)
"""
support_token_count = nb.feature_count_[0, :]

print(support_token_count)

against_token_count = nb.feature_count_[1, :]

print(against_token_count )

#Create a table with the results
tokens = pd.DataFrame({'token':X_train_tokens, 'support':support_token_count, 'against':against_token_count}).set_index('token')

#As it has too many members, we will try random samples
"""
print('Random sample')
print(tokens.sample(20, random_state=6))
"""

#We sum up 1 to avoid dividing by 0 or surrealistic results
tokens['support'] = tokens.support + 1
tokens['against'] = tokens.against + 1

#Calculates the frequency of each word to be in spam or ham
tokens['support'] = tokens.support / (nb.class_count_[0])
tokens['against'] = tokens.against / (nb.class_count_[1])

#Now, we can see frequency of each word
"""
print('Frequencies of each word in spam and ham')
print(tokens.sample(20, random_state=6))
"""

#Now we calculate the spam ratio
tokens['support_ratio'] = tokens.support / tokens.against
"""
print('Spam ratio of words')
print(tokens.sample(20, random_state=6))
"""
#Now we can look for the spamminess of one word in particular

print('Ratio of alquiler')
print(tokens.loc['alquiler', 'support_ratio'])

#Leave One out and Leave P Out examples

from sklearn.model_selection import LeaveOneOut

X_Leave1Out = np.array(trainset[0:100])
Y_Leave1Out = np.array(paraY1Out)

for train_index, test_index in loo.split(X_Leave1Out):
    #print ("Train: ", train_index, "Test: ", test_index)
    x_trainaux, x_testaux = X_Leave1Out[train_index],  X_Leave1Out[test_index]
    y_trainaux, y_testaux = Y_Leave1Out[train_index], Y_Leave1Out[test_index]
    #print(x_trainaux, x_testaux, y_trainaux, y_testaux)

from sklearn.model_selection import LeavePOut

lpo = LeavePOut(p=5)

X_LeavePOut = X_Leave1Out
Y_LeavePOut = Y_Leave1Out

lpo.get_n_splits(X_LeavePOut)

from sklearn.model_selection import ShuffleSplit
from sklearn.linear_model import SGDClassifier
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.pipeline import Pipeline

#Using a Shuffle Split permutation

ss = ShuffleSplit(n_splits=1, test_size=0.3, random_state=0)
X_ShuffleSplit = np.array(trainset)
Y_ShuffleSplit = Y_Leave1Out

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
    X_train_data.append(str(X_ShuffleSplit[index][0]))
    if X_ShuffleSplit[index][1] == 'aFavor':
        X_train_label.append(0)
    else:
        X_train_label.append(1)
for index in testAux:
    X_test_data.append(str(X_ShuffleSplit[index][0]))
    if X_ShuffleSplit[index][1] == 'aFavor':
        X_test_label.append(0)
    else:
        X_test_label.append(1)

#Training data
X_train_counts = vect.fit_transform(X_train_data)
tf_transformer = TfidfTransformer(use_idf=False).fit(X_train_counts)
X_train_tf = tf_transformer.transform(X_train_counts)
X_train_tf.shape
nb.fit(X_train_tf, X_train_label)

#Classifiyng new data
new = ['la gestación subrogada está bien','el vientre de alquiler está mal']
X_new_counts = vect.transform(new)
X_new_tfidf = tf_transformer.transform(X_new_counts)
predicted = nb.predict(X_new_tfidf)
print predicted

#Classifying training data
test_data = vect.transform(X_train_data)
test_tfi = tf_transformer.transform(test_data)
predicted = nb.predict(test_tfi)
print '\nAccuracy on predicting the training sentences'
print np.mean(predicted == X_train_label)
#print X_train_label
#print predicted

#Classifying test data
test_data = vect.transform(X_test_data)
test_tfi = tf_transformer.transform(test_data)
predicted = nb.predict(test_tfi)
print '\nAccuracy on predicting the test sentences'
print np.mean(predicted == X_test_label)

#Confusion matrix
print '\nConfusion Matrix'
print(metrics.confusion_matrix(X_test_label, predicted))

print '\nVisualización de clasificaciones incorrectas: '
#Results
contador = 0
for label1 in X_test_label:
    if label1 == 0:
        output = "A favor"
    else:
        output = "En Contra"
    if predicted[contador] == 0:
        output2 = "A favor"
    else:
        output2 = "En Contra"
    contador += 1
    if output != output2:
        print '\nClase esperada: ' + output + ' - Clase obtenida: '+output2
        print 'Frase: ' + X_test_data[contador] 


print X_test_label == predicted

#Pipeline example

from sklearn.linear_model import SGDClassifier
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.pipeline import Pipeline
textClassifier = Pipeline([('vect', CountVectorizer()),
                           ('tfidf', TfidfTransformer()),
                           ('clf', SGDClassifier())])

#Lime Docs Example

import lime
from sklearn import ensemble
from sklearn import feature_extraction
from lime.lime_text import LimeTextExplainer
from sklearn.datasets import fetch_20newsgroups

twenty_train = fetch_20newsgroups(subset='train', shuffle=True, random_state=42)
twenty_test = fetch_20newsgroups(subset='test', shuffle=True, random_state=42)

explainer = LimeTextExplainer(class_names=labels)
vectorizer = feature_extraction.text.TfidfVectorizer(lowercase=False)
rf = ensemble.RandomForestClassifier(n_estimators=500)
print 'Ha creado el clasificador'

train_vectors = vectorizer.fit_transform(twenty_train.data)
print 'Ha formateado los datos de entrenamiento'

test_vectors = vectorizer.transform(twenty_test.data)
print 'Ha formateado los datos de prueba'
rf.fit(train_vectors, twenty_train.target)
print'Ha sido entrenado'

pred = rf.predict(test_vectors)
print 'Ha clasificado'

explanation = explainer.explain_instance(twenty_train.data[0], pred, num_features=6)
print 'Ha creado la explicacion'