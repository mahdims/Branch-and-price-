# -*- coding: utf-8 -*-
"""
Created on Thu Jun 27 11:20:00 2019

@author: generic
"""

import cPickle as Pick
import time
import sys
import numpy as np
import math
#from Rangefinder import range_finder

def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)

def read_object(filename):
    with open(filename, 'rb') as input:
        obj= Pick.load(input)
    return  obj


New_dic={}
R=read_object("TObj_R_Van" )
Case_name="Van"  
for NN in [30]:#[60,30,15]:
#for ins_type in ["T"]:
    Time={15:1800,30:3600,60:7200}
    MaxTime=Time[NN]
    results={}
    M ={60: 9,30: 5,15: 3 }   # number of vehicles
    #M=3
    for inst in range(1,16):
        
        File_name= '%s_%d_%d_%d' %(Case_name,NN,M[NN],inst)  
        #File_name= '%s_%s_%d' %(Case_name,ins_type,inst)  
        #Data=read_object('G:\My Drive\\1-PhD thesis\equitable relief routing\Code\%s\%s' %(Case_name,File_name) ) 
        #Data.Gamma=0.1
        
        if inst<=5:
            New_dic[File_name]=R[File_name]/100
        elif inst<=10:
            New_dic[File_name]=(0.8+ 0.4* np.random.rand())*New_dic['%s_%d_%d_%d' %(Case_name,NN,M[NN],inst-5)  ]
        else:
            VTLR=read_object("TObj_R_VanVTL30" )
            
            New_dic[File_name]=VTLR[File_name]
            
save_object(New_dic, "TObj_R_Van30")
        
        