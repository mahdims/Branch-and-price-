from time import time
from Real_Input import Real_Input
from Model2 import Model2
from Model1_V2 import Model1_V2
from Model1 import Model1
import math
import numpy as np
import os
import pickle as Pick


def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)


def read_object(filename):
    with open(filename, 'rb') as file:
        obj = Pick.load(file, encoding='latin1')
    return obj


Case_name = "Van"
#Case_name = "Kartal"
#R_dic=read_object("TObj_R_Kartal" )
NN = 13
ins_type = "T"
CWD = os.getcwd()
# for ins_type in ["T","VT"]:#[15,30]:#[60,30,15]:
for NN in [15]:
    results = {}
    M = {60: 9, 30: 5, 15: 3}   # number of vehicles
    for inst in [15]:
        File_name = '%s_%d_%d_%d' % (Case_name, NN, M[NN], inst)
        # File_name= '%s_%s_%d' %(Case_name,ins_type,inst)
        path2file = CWD.replace("Mathematical_Models", "Data") + f"/{Case_name}/{File_name}"
        Data = read_object(path2file)

        if inst <= 5:
            ins_type = "T"
        elif inst <= 10:
            ins_type = "VT"
        else:
            ins_type = "VTL"
        
        R_dic = read_object("TObj_R_Van%s"%(NN) )
        Data.Gamma = 0  # for Kratal 1 , for Van 0.1
        # Data.Lambda = 0
        zeta1 = 2
        if ins_type == "T":
            zeta2 = 0.1
        if ins_type == "VT":
            zeta2 = 0.2
        if ins_type == "VTL":
            zeta2 = 0.2
            zeta1 = 1
            
        Data.Maxtour = zeta1*math.ceil(float(NN)/M[NN]) * np.percentile(list(Data.distances.values()), 50)
        Data.Q = zeta2 * Data.G.nodes[0]['supply']/M[NN]
        Data.Total_dis_epsilon = 0.85 * M[NN]*Data.Maxtour
        
        R = R_dic[File_name]
        
        # Data.Q = max(math.ceil(Data.total_demand / float(Data.M) ) , max(dict(Data.Gc.nodes(data='demand')).values())  )
        start = time()
        best_obj, LB, Runtime, GAP = Model1(Data, R)
        # best_obj ,LB ,Runtime ,GAP = Model2(Data,R)
        # best_obj ,LB ,Runtime ,GAP = Model1_V2(Data,R)
        #oldresult=read_object('G:\My Drive\\1-PhD thesis\equitable relief routing\Code\%s\%s_BnPresult' %(Case_name,File_name)  )
        
        results[File_name] = [best_obj, LB, Runtime, GAP]
        #oldresult[File_name][0]=  best_obj
        #results=oldresult
        Model_runtime = time()-start
        
        
        #save_object(results,'G:\My Drive\\1-PhD thesis\\2 - equitable relief routing\Code\%s\%s_NewModel' %(Case_name,File_name) )
        
        #save_object(results,'G:\My Drive\\1-PhD thesis\\2 - equitable relief routing\Code\%s\%s_Modelresult' %(Case_name,File_name) )        




