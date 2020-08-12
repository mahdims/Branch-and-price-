# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 09:29:24 2019

@author: User
"""
import sys
sys.path.insert(0, 'G://My Drive//1-PhD thesis//equitable relief routing//Code//SingleObj')
import math
from feasibleSol import Initial_feasibleSol
from ColumnGeneration import ColumnGen
from Master import MasterModel
from Sub import SubProblem
from copy import copy
import numpy as np
import itertools as it
from Real_Input import Real_Input
import cPickle as Pick
from Obj_Calc import objvalue
def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)
        
        
def read_object(filename):
    with open(filename, 'rb') as input:
        obj= Pick.load(input)
    return  obj



def range_finder(Data,kere):
    global TravelObj
    
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
        table.append(objvalue(Data,Y, Col_dic2))
    
    table=np.array(table)
    Objrange={}
    for i,a in enumerate(["Total_time","equity"]):
        Objrange[a]= np.abs(table[0,i]-table[1,i])
    
    return Objrange   
    
R={}
N=13
M=3
# ["T","VT","VTL"]:
kere=1
global TravelObj
TravelObj=[]
for NN in [60]:
    M ={60: 9, 30: 5,15: 3 }   # number of vehicle
    for inst in range(11,16):
        
        if inst<=5:
            ins_type="T"
        elif inst<=10:
            ins_type="VT"
        else:
            ins_type="VTL"
        
        
        zeta1 = 2
        if ins_type=="T":
            zeta2 = 0.5
        if ins_type=="VT":
            zeta2 = 0.2    
        if ins_type=="VTL":
            zeta2 = 0.2
            zeta1 = 1
            
        File_name= 'Van_%d_%d_%d' %(NN,M[NN],inst)  
        #File_name= 'Kartal_%s_%d' %(ins_type,inst)  

        Data=read_object('G:\My Drive\\1-PhD thesis\equitable relief routing\Code\Van\%s' %File_name) 

        Data.Q=zeta2 * Data.G.node[0]['supply']/M[NN] # very tight capacity for instanc 6-10

        Data.Maxtour=zeta1* math.ceil(NN/M[NN]) * np.mean(Data.distances.values())  
        
        Data.Total_dis_epsilon= 0.85 * M[NN]*Data.Maxtour

        R[File_name] = range_finder(Data,kere)["Total_time"]/100
        kere += 1
        save_object(R, "TObj_R_Van%s%s_%s"%(ins_type,NN,inst) )
