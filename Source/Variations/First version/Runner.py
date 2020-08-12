# -*- coding: utf-8 -*-
"""
Created on Fri Nov 09 17:31:32 2018

@author: generic
    """
from time import time
from Input import Input
from Model2 import Model2
from Model1 import Model1
from Model1_V2 import Model1_V2
import math
import numpy as np 
#from BnP import branch_and_bound
import cPickle as Pick
def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)

def read_object(filename):
    with open(filename, 'rb') as input:
        obj= Pick.load(input)
    return  obj

#NN=40 # number of nodes
#M=8 # number of vehicles 
#Q=50 # vehicles Capacity
#C=0.75 # percentage of demand as Initial inventory in depot
#Lambda=0.5
#Gamma=2
#Data=Input(NN,M,Q,C,Lambda)
#Data = read_object('Data.pkl_%d_%d_%d' %(NN,M,Q) ) # read Data stored in directory 
#Case_name = "Van"
Case_name = "Kartal"
R_dic=read_object("TObj_R_Kartal" )
ins_type= "T"
#for ins_type in ["T","VT"]:#[15,30]:#[60,30,15]:
for NN in [13]:
    results={}
    M ={60: 9, 30: 5, 15: 3 ,13:3 }   # number of vehicles
    #M=3
    for inst in [12]:
        '''
        if inst<=5:
            ins_type="T"
        elif inst<=10:
            ins_type="VT"
        else:
            ins_type="VTL"       

        '''    
        if inst<=10:
            ins_type="T"
        elif inst<=20:
            ins_type="VT"
            inst-=10
        else:
            ins_type="VTL"
            inst-=20

        #File_name= '%s_%d_%d_%d' %(Case_name,NN,M[NN],inst)
        File_name= '%s_%s_%d' %(Case_name,ins_type,inst)
        Data=read_object('G:\My Drive\\1-PhD thesis\\2 - equitable relief routing\Code\%s\%s' %(Case_name,File_name) ) 

        Data.Gamma=0

        for i in range(1,NN):
            Data.distances[(i,NN+1)] = Data.distances[(0,i)]
        
        #R_dic=read_object("TObj_R_Van%s"%(NN) )
        
        zeta1=2
        if ins_type=="T":
            zeta2=0.5
        if ins_type=="VT":
            zeta2=0.2
        if ins_type=="VTL":
            zeta2=0.2
            zeta1=1
            
        #Data.Maxtour= zeta1*math.ceil(float(NN)/M) * np.percentile(Data.distances.values(),50) 
        Data.Maxtour= zeta1*math.ceil(float(NN)/M[NN]) * np.percentile(Data.distances.values(),50) 
        #Data.Q= zeta2 * Data.G.node[0]['supply']/M # very tight capacity for instanc 6-10
        Data.Q= zeta2 * Data.G.node[0]['supply']/M[NN]
        #Data.Total_dis_epsilon= 0.85* M*Data.Maxtour#0.85 * M*Data.Maxtour
        Data.Total_dis_epsilon= 0.85* M[NN]*Data.Maxtour
        
        R=R_dic[File_name ]
        start= time()
        #best_obj ,LB ,Runtime ,GAP = Model1(Data,R)
        best_obj ,LB ,Runtime ,GAP = Model2(Data,R)
        #best_obj ,LB ,Runtime ,GAP = Model1_V2(Data,R)
        #oldresult=read_object('G:\My Drive\\1-PhD thesis\equitable relief routing\Code\%s\%s_BnPresult' %(Case_name,File_name)  )
        print('%s %s %s %s %s' %(File_name,best_obj ,LB ,Runtime ,GAP ))
        results[File_name]=[best_obj ,LB ,Runtime ,GAP]
        #results[c]=[best_obj ,LB ,Runtime ,GAP]
        #oldresult[File_name][0]=  best_obj
        #results=oldresult
        Model_runtime=time()-start
        #save_object(results,'G:\My Drive\\1-PhD thesis\\2 - equitable relief routing\Code\%s\%s_NewModel' %(Case_name,File_name) )
        
        #save_object(results,'G:\My Drive\\1-PhD thesis\\2 - equitable relief routing\Code\%s\%s_Modelresult' %(Case_name,File_name) )        
