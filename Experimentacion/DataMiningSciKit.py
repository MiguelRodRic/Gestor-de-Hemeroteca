# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 17:00:48 2017

@author: Miguel
"""
#The aim of this program is to do some data mining with naive bayes
#And logistic regression plus sci kit
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd 

#Data and most of the code obtain from https://github.com/justmarkham/pycon-2016-tutorial
url = 'https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv'
sms = pd.read_table(url, header=None, names=['label', 'message'])

"""
print(sms.shape)
"""
"""
print(sms.label.value_counts())
"""
#We assign ham messages one value and spam messages another value
sms['label_num'] = sms.label.map({'ham':0, 'spam':1})

X = sms.message
Y = sms.label_num

"""
print(X.shape)
print(Y.shape)
"""

from sklearn.cross_validation import train_test_split
#Split the data to obtain training messages, training labels, test messages and test labels
X_train, X_test, Y_train, Y_test = train_test_split(X, Y, random_state=1)
"""
print(X_train.shape)
print(X_test.shape)
print(Y_train.shape)
print(Y_test.shape)
"""
vect = CountVectorizer()

#Learns the training data and creates a document-term matrix from it in one step
X_train_dtm = vect.fit_transform(X_train)

#Same thing with the testing data
X_test_dtm = vect.transform(X_test)



#Now we build the model
#Imports of naive bayes
from sklearn.naive_bayes import MultinomialNB
nb = MultinomialNB()

#Naive Bayes is much faster than other alternatives
nb.fit(X_train_dtm, Y_train)

#Make class predictions from X_test_dtm
Y_pred_class = nb.predict(X_test_dtm)

#Calculate accuracy
from sklearn import metrics
"""
print(metrics.accuracy_score(Y_test, Y_pred_class))

#Confusion matrix
print(metrics.confusion_matrix(Y_test, Y_pred_class))

#print false positives
print(X_test[(Y_pred_class==1) & (Y_test==0)])
"""
#Also 
"""
print(X_test[Y_pred_class > Y_test])
"""

#For false negatives
"""
print(X_test[Y_pred_class < Y_test])
"""

#Compared with logistic regression

from sklearn.linear_model import LogisticRegression
logreg = LogisticRegression()

#Prepares training data, for labels and messages
logreg.fit(X_train_dtm, Y_train)

#Make class predictions for X_test_dtm
Y_pred_class = logreg.predict(X_test_dtm)

#Calculate predicted probabilities for X_test_dtm
y_pred_prob = logreg.predict_proba(X_test_dtm)[:,1]
"""
print(y_pred_prob)
"""
#Accuracy without calibration
"""
print(metrics.accuracy_score(Y_test, Y_pred_class))
"""
#Accuracy with calibration
"""
print(metrics.roc_auc_score(Y_test, y_pred_prob))
"""

#Examining model for spamminess of new tokens
#store the vocabulary of X_train
X_train_tokens = vect.get_feature_names()


#Count the number of appereances of each token in ham and spam
"""
print(nb.feature_count_)
"""
ham_token_count = nb.feature_count_[0, :]
"""
print(ham_token_count)
"""
spam_token_count = nb.feature_count_[1, :]
"""
print(spam_token_count )
"""
#Create a table with the results
tokens = pd.DataFrame({'token':X_train_tokens, 'ham':ham_token_count, 'spam':spam_token_count}).set_index('token')

#As it has too many members, we will try random samples
"""
print('Random sample')
print(tokens.sample(20, random_state=6))
"""

#We sum up 1 to avoid dividing by 0 or surrealistic results
tokens['ham'] = tokens.ham + 1
tokens['spam'] = tokens.spam + 1

#Calculates the frequency of each word to be in spam or ham
tokens['ham'] = tokens.ham / (nb.class_count_[0])
tokens['spam'] = tokens.spam / (nb.class_count_[1])

#Now, we can see frequency of each word
"""
print('Frequencies of each word in spam and ham')
print(tokens.sample(20, random_state=6))
"""

#Now we calculate the spam ratio
tokens['spam_ratio'] = tokens.spam / tokens.ham
"""
print('Spam ratio of words')
print(tokens.sample(20, random_state=6))
"""
#Now we can look for the spamminess of one word in particular
"""
print('Spamminess of dating')
print(tokens.loc['dating', 'spam_ratio'])
print('Spamminess of money')
print(tokens.loc['money', 'spam_ratio'])
print('Spamminess of free')
print(tokens.loc['free', 'spam_ratio'])
print('Spamminess of call')
print(tokens.loc['call', 'spam_ratio'])
"""
