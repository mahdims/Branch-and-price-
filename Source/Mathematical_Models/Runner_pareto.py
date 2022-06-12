from time import time
from Model2 import Model2
from Model1_V2 import Model1_V2
from Model1 import Model1
import os
import sys
BASEDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, BASEDIR)
from utils import utils, plots
import json


def Epsilon_method(Data):

    _, _, Runtime1, _, f1_max, f2_min = Model1_V2(Data, Data.R, SecondObjOnly=True)
    _, _, Runtime2, _, f1_min, f2_max = Model1_V2(Data, Data.R, FirstObjOnly=True)
    two_obj = {f2_max: [f1_min, f2_max, Runtime2]}
    two_obj ={}
    N_big = 10000
    Step_big = int((f2_max-f2_min)/N_big)
    Step_big = 1
    epsilon = f2_max - Step_big
    while epsilon > f2_min:
        Data.Total_dis_epsilon = epsilon
        best_obj, LB, Runtime, GAP, Gini, TT_time = Model1_V2(Data, Data.R)
        print(f"The optimal objective is {best_obj}, Gini: {Gini} TT: {TT_time}")
        two_obj[epsilon] = [Gini, TT_time, Runtime]

        if TT_time < epsilon - Step_big:
            epsilon = TT_time - Step_big
        else:
            epsilon = epsilon - Step_big

    return two_obj


def write_dic(Fname,two_obj):

    with open(BASEDIR+f'/Data/Bi_Obj_results/{Fname}_2OBJ.txt', 'w') as file:
        file.write(json.dumps(two_obj))


def read_dic(Fname):
    with open(BASEDIR+f'/Data/Bi_Obj_results/{Fname}_2OBJ.txt', 'r') as file:
        two_objs = json.load(file)
    return two_objs


if __name__ == "__main__":
    BASEDIR = os.path.dirname(BASEDIR)
    #Case_name = "Van"
    Case_name="Kartal"
    NN = 13
    for NN in [13]: # [60,30,15]:
        Time = {15: 1000, 13: 1000, 30: 1800, 60: 3600}
        MaxTime = Time[NN]
        M = {60: 9, 30: 5, 15: 3, 13: 3}
        for inst in [1]:
            Data, File_name = utils.data_preparation(Case_name, NN, M[NN], inst)
            print(f"We are solving {File_name}")
            two_obj = Epsilon_method(Data)
            write_dic(File_name, two_obj)
            #two_obj = read_dic(File_name)
            for ep, val in two_obj.items():
                print(f"Epsilon : {ep} -> Gini: {round(val[0], 2)} Total travel time : {val[1]} Solve Time : {round(val[2])}")
            plots.pareto_plot(two_obj)
