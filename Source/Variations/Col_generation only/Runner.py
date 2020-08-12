# -*- coding: utf-8 -*-
"""
Created on Fri Nov 09 17:31:32 2018

@author: generic
    """
from time import time
from Input import Input
from Model2 import Model2
from ColumnGeneration import ColumnGen
import cPickle as Pick

def read_object(filename):
    with open(filename, 'rb') as input:
        obj= Pick.load(input)
    return  obj


NN=10 # number of nodes
M=3 # number of vehicles 
Q=150 # vehicles Capacity
C=0.75 # percentage of demand as Initial inventory in depot
Lambda=0.5
Data=Input(NN,M,Q,C,Lambda)
#Data=read_object('Model_Data.pkl') # read Data stored in directory 
epsilon=500

start=time()
#ModelObjval=Model2(Data,epsilon)
Model_runtime=time()-start
print("Model Runtime: %f" %Model_runtime)
start=time()
ColGObjval=ColumnGen(Data,epsilon)
ColumnGen_runtime=time()-start

#print("Model optimal value: %f" %ModelObjval)
#print("Model Runtime: %f" %Model_runtime)
print("N = %d , M = %d" %(NN,M))
print("Column Generation optimal value: %f" %ColGObjval)
print("Column Generation Runtime: %f" %ColumnGen_runtime)