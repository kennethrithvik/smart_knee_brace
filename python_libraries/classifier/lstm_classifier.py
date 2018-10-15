
# coding: utf-8

# In[1]:


import sqlite3
import pandas as pd
# Create your connection.
cnx = sqlite3.connect('../sql_mqtt_data_log/sensor.db')

df_walking = pd.read_sql_query("SELECT * FROM ction", cnx)
#df_standing = pd.read_sql_query("SELECT * FROM standing", cnx)
#df_complete=pd.concat([df_walking,df_standing],axis=0)


# In[3]:


#print(df_walking.head())
#print(df_standing.head())
df_walking


# In[95]:



import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import tensorflow as tf  # Version 1.0.0 (some previous versions are used in past commits)
from sklearn import metrics
from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from keras.layers import Dense, Dropout, LSTM, Embedding
from keras.preprocessing.sequence import pad_sequences
from keras.models import Sequential
from sklearn.metrics import classification_report,confusion_matrix

import os


# In[97]:


X_train=df_complete.drop(['action','id','bottom_temperature','top_temperature','timestamp'],axis=1)
Y_train=df_complete['action']
#Y_train[Y_train=='walking']=0
#Y_train[Y_train=='standing']=1
Y_train=pd.get_dummies(Y_train)
X_train=(X_train-X_train.min())/(X_train.max()-X_train.min())
X_train, X_test, Y_train, Y_test = train_test_split(X_train, Y_train, test_size=0.2)
X_train=X_train.values
Y_train=Y_train.values
X_test=X_test.values
Y_test=Y_test.values
Y_test


# In[98]:


def create_model(input_length):
    print ('Creating model...')
    model = Sequential()
    model.add(Embedding(input_dim = 188, output_dim = 50, input_length = input_length))
    model.add(LSTM(output_dim=256, activation='sigmoid', inner_activation='hard_sigmoid', return_sequences=True))
    model.add(Dropout(0.5))
    model.add(LSTM(output_dim=256, activation='sigmoid', inner_activation='hard_sigmoid'))
    model.add(Dropout(0.5))
    model.add(Dense(2, activation='softmax'))

    print ('Compiling...')
    model.compile(loss='binary_crossentropy',
                  optimizer='rmsprop',
                  metrics=['accuracy'])
    return model
model = create_model(len(X_train[0]))


# In[99]:


hist = model.fit(X_train, Y_train, batch_size=10, epochs=10, validation_split = 0.1, verbose = 1)

score, acc = model.evaluate(X_test, Y_test, batch_size=1)
print('Test score:', score)
print('Test accuracy:', acc)


# In[100]:


Y_pred=model.predict(X_test)


# In[102]:


Y_pred = np.argmax(Y_pred,axis = 1) 
Y_test=np.argmax(Y_test,axis=1)


# In[104]:


print('Test set classification report:\n{}'.format(classification_report(Y_test, Y_pred)))
print('Confusion Matrix:\n{}'.format(confusion_matrix(Y_test, Y_pred)))
Y_pred

