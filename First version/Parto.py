# -*- coding: utf-8 -*-
"""
Created on Sun Jun 30 23:48:13 2019

@author: User
"""
from Node import Node
from Real_Input import Real_Input
from BnP import branch_and_bound
from Obj_Calc import Obj_Calc ,objvalue
import numpy as np
import math
import cPickle as Pick

def read_object(filename):
    with open(filename, 'rb') as input:
        obj= Pick.load(input)
    return  obj





Case_name="Kartal"
R_dic=read_object("TObj_R_Kartal" )
NN=13
MaxTime=2000
M ={60: 9,30: 5,15: 3 ,13:3}   # number of vehicles
inst=4
ins_type="VT"
File_name= '%s_%s_%d' %(Case_name,ins_type,inst) 
#File_name= '%s_%d_%d_%d' %(Case_name,NN,M[NN],inst)  
#R_dic=read_object("TObj_R_Van%s"%(NN) )
R=R_dic[File_name  ] 
#out=[]
runresults={}
Data=read_object('G:\My Drive\\1-PhD thesis\equitable relief routing\Code\%s\%s' %(Case_name,File_name) ) 
'''      
if inst<=5:
    ins_type="T"
elif inst<=10:
    ins_type="VT"
else:
    ins_type="VTL"
'''

zeta1=2
if ins_type=="T":
    zeta2=0.5
if ins_type=="VT":
    zeta2=0.2
if ins_type=="VTL":
    zeta2=0.2
    zeta1=1

Data.Gamma=1
Data.Maxtour= zeta1*math.ceil(float(NN)/M[NN]) * np.percentile(Data.distances.values(),50)   
Data.Q=zeta2 * Data.G.node[0]['supply']/M[NN] 

for epsilon in [50000, 45000 , 40000 ,  35000 , 30000,   25000,   20000,      15000]:
    Data.Total_dis_epsilon= epsilon

    Bsolution , best_obj ,LB ,best_objtime ,Runtime ,GAP = branch_and_bound(Data,R,MaxTime)
    runresults["%s" %epsilon]=[Bsolution , best_obj ,LB ,best_objtime ,Runtime ,GAP]
    dic={}
    y=[]
    for i,r in enumerate(Node.best_Route):
        dic[i]=r
        y.append(i)

    out.append( [epsilon] + list(objvalue( Data , y , dic ))    )
    
out=np.array(out)


















