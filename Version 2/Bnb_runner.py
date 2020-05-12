
import cPickle as Pick
import time
from BnP import branch_and_bound
import numpy as np
import math


def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)


def read_object(filename):
    with open(filename, 'rb') as input:
        obj = Pick.load(input)
    return obj
    
def test_the_distance_symmetry(Dis):
    for i,j in Dis.keys():
        if i<j :
            if Dis[i,j] != Dis[j,i]:
                print("Not symmetrical distances")
                break

def print_the_solution(Sol):
    Sol

#Case_name="Van"
Case_name="Kartal"
R_dic=read_object("G:\My Drive\\1-PhD thesis\\2 - Equitable relief routing\Code\TObj_R_Kartal" )
NN=13
#for NN in [13]:#[60,30,15]:
for ins_type in ["T"]:
    Time={15:3600,13:3600,30:3600,60:7200}
    MaxTime=Time[NN]
    results={}
    M ={60: 9,30: 5,15: 3, 13:3 }   # number of vehicles
    #M=3
    for inst in [12]:#[1,3,4,10]:#range(15,16):
        '''
        if inst <= 5:
            ins_type = "T"
        elif inst <= 10:
            ins_type = "VT"
        else:
            ins_type = "VTL"

        '''
        # For Kartal case
        if inst<=10:
            ins_type="T"
        elif inst<=20:
            ins_type="VT"
            inst-=10
        else:
            ins_type="VTL"
            inst-=20

        File_name= '%s_%s_%d' %(Case_name,ins_type,inst)
        #File_name = '%s_%d_%d_%d' %(Case_name,NN,M[NN],inst)
        #R_dic = read_object("G:\My Drive\\1-PhD thesis\\2 - Equitable relief routing\Code\TObj_R_Van%s" %NN )
        R = R_dic[File_name ]
        
        Data = read_object('G:\My Drive\\1-PhD thesis\\2 - equitable relief routing\Code\%s\%s' %(Case_name,File_name) )

        # If the distance are symmetric
        #test_the_distance_symmetry(Data.distances)

        # please make sure that this won't effect any thing (Making the i,NN+1 arc zero )
        for i in range(NN):
            Data.distances[i, NN+1] = 0
        Data.Gamma = 0 # for Kratal 1 , for Van 0.1
        #Data.Lambda = 0
        zeta1 = 2
        if ins_type == "T":
            zeta2 = 0.5
        if ins_type == "VT":
            zeta2 = 0.2
        if ins_type == "VTL":
            zeta2 = 0.2
            zeta1 = 1
         
        Data.Maxtour = zeta1*math.ceil(float(NN)/M[NN]) * np.percentile(Data.distances.values(),50)
        #Data.Maxtour= zeta1*math.ceil(float(NN)/M) * np.percentile(Data.distances.values(),50) 
        Data.Q = zeta2 * Data.G.node[0]['supply']/M[NN]
        #Data.Q= zeta2 * Data.G.node[0]['supply']/M # very tight capacity for instanc 6-10
        Data.Total_dis_epsilon = 0.85*M[NN]*Data.Maxtour
        #Data.Total_dis_epsilon= 0.85* M*Data.Maxtour

        R = R_dic[File_name]

        start = time.time()
        Bsolution, best_obj, LB, best_objtime, Runtime, GAP = branch_and_bound(Data,R,MaxTime)
        results[File_name] = [Bsolution, best_obj, LB, best_objtime, Runtime, GAP]
        RunTime_BnB = time.time()-start
        print_the_solution(Bsolution)
        #save_object(results,'G:\My Drive\\1-PhD thesis\equitable relief routing\Code\%s\%s_%s_%s_BnPresultp3' %(Case_name,Case_name,NN,inst) )
        #save_object(results,'G:\My Drive\\1-PhD thesis\equitable relief routing\Code\%s\%s_BnPresult' %(Case_name,File_name) )
#save_object(R, "TObj_R_Kartal" )