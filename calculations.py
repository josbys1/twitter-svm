# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 15:01:36 2015

@author: josbys1
"""
import re
import time
import pprint
import random
from scipy import stats
import math
from credentials import keys
import tweepy
import numpy
import sys
from sklearn.externals import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import LinearSVC,SVC
from sklearn.svm import SVC
from sklearn.metrics import confusion_matrix
from sklearn import cross_validation,metrics,grid_search,linear_model
from TweetObj import Tweet
import matplotlib
import matplotlib.pyplot as plt
import plotcm

def readFromMemory(location):
    return joblib.load("data/"+location +'.pkl')

def store(tweets,location):
    joblib.dump(tweets,location+'.pkl')

def getX(tweets):
    a=[]
    for obj in tweets:
        a.append(obj.text)
    return a

def getY(tweets):
    a=[]
    for obj in tweets:
        a.append(obj.author)

    return numpy.asarray(a)

def vectorize(tweets):
    vectorizer = CountVectorizer(analyzer='word')
    fit_vectorizer = vectorizer.fit(getX(tweets))
    ft = numpy.array(fit_vectorizer.transform(getX(tweets)).toarray())
    print("Vectorized!")
    for i in range(0,len(tweets)-1):
        tweets[i].vector = ft[i]
    return (fit_vectorizer,ft)

def split(tweets):
    x=getY(tweets)
    return vectorize(tweets),x

def gs(X,Y,folds,parameters):
    cv=cross_validation.KFold(len(X), n_folds=folds,shuffle=True,random_state=None)
    svr = SVC()
    clf = grid_search.GridSearchCV(svr, parameters,cv=cv)
    print("About to fit...")
    clf.fit(X,Y)
    pprint.pprint(clf.grid_scores_)
    pprint.pprint(clf.best_params_)

def regularSVM(X,Y,c,pctTest,shouldReturnMetrics):
    #svm = LinearSVC(C=c);
    svm=linear_model.LogisticRegression(C=c);
    cv=X_train, X_test, Y_train, Y_test = cross_validation.train_test_split(X,Y, test_size=pctTest, random_state=None)
    svm.fit(X_train,Y_train)
    y_pred=svm.predict(X_test)
    channels=svm.classes_
    channels.sort()
    getWrongValues(y_pred,Y_test,channels,shouldReturnMetrics,num=len(X))
    return svm

def showCoefficients(svm,vectorizer):
    #Deal with binary class coefficients
    channels=svm.classes_
    channels.sort()
    for i in range(0,len(channels)):
        coef=svm.coef_[i]
        indices=numpy.argsort(coef)
        sorted_coef=coef[indices]
        sorted_features=numpy.array(vectorizer.get_feature_names())[indices]
        
        print("Positive 5 FW for " + channels[i])
        for y in range(len(sorted_coef)-6,len(sorted_coef)):
            print(sorted_features[y])
        print("\n")
        
        print("Negative 5 FW for " + channels[i])
        for x in range(0,5):
            print(sorted_features[x])
        print("\n")
        
def showBinaryCoefs(svm,vectorizer):
    channels=svm.classes_
    channels.sort()
    coef=svm.coef_[0]
    indices=numpy.argsort(coef)
    sorted_coef=coef[indices]
    sorted_features=numpy.array(vectorizer.get_feature_names())[indices]
    print("Positive 10 feature weights for " + channels[0])
    for x in range(0,10):
        print(sorted_features[x])
    print("Negative 10 feature weights for " + channels[0])
    for y in range(len(sorted_coef)-11,len(sorted_coef)):
        print(sorted_features[y])


def crossValidate(X,Y,folds=10,c=1):
    svm=LinearSVC(C=c)
    cv=cross_validation.KFold(len(X), n_folds=folds,shuffle=True,random_state=None)
    for i in cross_validation.cross_val_score(svm,X,Y,cv=cv):
        print(i)

def predict(x_test,model):
    return model.predict(x_test)

def getWrongValues(pred_values,y_test,channels,shouldReturnMetrics=True,num=0):
    count_wrong=0
    if(shouldReturnMetrics):
        print("Accuracy percentage: " + str(metrics.accuracy_score(y_test, pred_values, normalize=True, sample_weight=None)))
        # Compute confusion matrix
        cm = confusion_matrix(pred_values, y_test,labels=channels)
        numpy.set_printoptions(precision=2)
        print('Confusion matrix, without normalization')
        print(cm)
        plt.figure()
        #plotcm.plot_confusion_matrix(cm,channels,title="Confusion matrix: n=" + str(num/len(channels)),filename="cm"+(str(num/len(channels))))
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, numpy.newaxis]
        plotcm.plot_confusion_matrix(cm_normalized, channels, title='Normalized confusion matrix, n='+str(num/len(channels)),filename="cm"+(str(num/len(channels)))+"norm.png")
def predictTweet(svm,vectorizer):
    while True:
        test=[re.sub(r"(?:\@|https?\:\/\/)\S+", "URL",input("Type a message: "))]
        if(test[0]==-1):
            return
        v=vectorizer.transform(test).toarray()
        print(v)
        print(svm.predict(vectorizer.transform(test).toarray()))
        z=sorted(zip(svm.classes_,svm.predict_proba(vectorizer.transform(test).toarray())[0]), key=lambda tup: tup[1])
        for i in reversed(range(len(z)-4,len(z))):
            print(z[i][0] + ": {0:.0f}%".format(z[i][1]*100))

def testOverN(X,Y,c,pctTest,channels,shouldReturnMetrics=False,increment=100):
    for i in xrange(100,len(X),50):
        start = time.time()
        svm = LinearSVC(C=c);
        cv=X_train, X_test, Y_train, Y_test = cross_validation.train_test_split(X[:i],Y[:i], test_size=pctTest, random_state=None)
        svm.fit(X_train,Y_train)
        y_pred=svm.predict(X_test)
        print(str(i) + "," + str(metrics.accuracy_score(Y_test, y_pred, normalize=True, sample_weight=None))+","+str(time.time()-start))