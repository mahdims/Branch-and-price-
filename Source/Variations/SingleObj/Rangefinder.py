# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 09:29:24 2019

@author: User
"""
import sys
sys.path.insert(0, 'G://My Drive//1-PhD thesis//equitable relief routing//Code//SingleObj')

from feasibleSol import Initial_feasibleSol
from ColumnGeneration import ColumnGen
from Master import MasterModel
from Sub import SubProblem
from copy import copy
import numpy as np
import itertools as it
from Real_Input import Real_Input
import cPickle as Pick

def read_object(filename):
    with open(filename, 'rb') as input:
        obj= Pick.load(input)
    return  obj

def objvalue(Data,obj_name,Y, Col_dic):
     Gc=Data.Gc
     G=Data.G
     Lambda = Data.Lambda
     TotalD=Data.total_demand
     
     Travel_time=sum( [Col_dic[r].travel_time*Y[r] for r in Col_dic.keys()]  ) 
        
    
     inx=[ i  for i in Y.keys() if Y[i]!=0]
     Del= np.array( [ np.array(Col_dic[i].RDP)* Y[i] for i in inx] )
     Del=np.sum(Del, axis=0)
     
     gini=[]
     for i,j in it. product(Gc.nodes,repeat=2):
        gini.append( abs( Del[i]*G.node[j]['demand'] - Del[j]*G.node[i]['demand']  ) )
            
     Equity = sum( [Gc.node[i]['demand'] - Del[i]  for i in Gc.nodes]) + (Lambda/TotalD)*sum(gini)  

     return(Travel_time,Equity)

def range_finder(Data):
    
    Col_dic={}
    New_Col, _ = Initial_feasibleSol(Data,RDP=None)
    for inx,R_D in enumerate(New_Col):
            Col_dic[inx+1] = copy(R_D)
    
    
    table=[]
     
    for obj_name in ["Total_time","equity"]:
    
        RMP , (y,tp,tn) = MasterModel(Data , Col_dic , obj_name)
        Sub , x , q , a = SubProblem( Data )
        (feasible, Objval, Y, Col_dic2) = ColumnGen(Data,obj_name, RMP,Col_dic, (Sub , x , q , a) , (y,tp,tn))    
        print(Objval)
        table.append(objvalue(Data,obj_name,Y, Col_dic2))
    
    table=np.array(table)
    Objrange={}
    for i,a in enumerate(["Total_time","equity"]):
        Objrange[a]= np.abs(table[0,i]-table[1,i])
    
    return Objrange    

