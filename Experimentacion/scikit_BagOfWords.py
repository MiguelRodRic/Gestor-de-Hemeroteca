# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 18:32:37 2017

@author: Miguel
"""

#Example of bag of words

#Training texts
recipes = ['pizza of corn, pepper and tuna',
                'tuna and tomatoe salad',
                'chicken sandwich',
                'roasted chicken with honey',
                'tuna sandwich',
                'pasta with tomato sauce',
                'steak with corn and pepper',
                'roasted potato with paprika',
                'steak with mashed potato',
                'mushrooms with rice',
                'chicken tacos']

#The aim isto use count vectorizer to convert text into matrix
from sklearn.feature_extraction.text import CountVectorizer

import pandas as pd 

#We remove the training words we don't care about 
vect = CountVectorizer(stop_words=['with', 'and', 'of'])

#Learn the vocabulary of the training
vect.fit(recipes)


#examine the fitted vocabulary
text = vect.get_feature_names()
print('')
print('')
print('Training text alphabetically organised')
print(text)


#transform training data into a 'document-term matrix'
#Sparse matrix only records the coordenates with a 1
recipes_dtm = vect.transform(recipes)

#Convert sparse matrix to a dense matrix
#Dense matrix records the frequency whether it's 0 or not
dtm_array = recipes_dtm.toarray()
print('')
print('')
print("Dense matrix of the training data")
print(pd.DataFrame(recipes_dtm.toarray(), columns=vect.get_feature_names()))


#Test text
simple_test = ["Grilled steak with chicken wings, chicken breast, and chicken legs with honey"]

#Sparse matrix with the frequency of the test, compared with the results
simple_text_dtm = vect.transform(simple_test)
print('')
print('')
print("Text vector, ready for testing")
print(simple_text_dtm.toarray())



print('')
print('')
print("Frequency results of the test recipe seen from the training text matrix")
print(pd.DataFrame(simple_text_dtm.toarray(), columns=vect.get_feature_names()))