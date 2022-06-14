"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""

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
import glob


def Epsilon_method(Data, UseModel2=False):

    if UseModel2:
        Model = Model2
    else:
        Model = Model1_V2

    _, _, Runtime1, _, f1_max, f2_min = Model(Data, Data.R, SecondObjOnly=True)
    _, _, Runtime2, _, f1_min, f2_max = Model(Data, Data.R, FirstObjOnly=True)
    two_obj = {f2_max: [f1_min, f2_max, Runtime2], f2_min: [f1_max, f2_min,Runtime1]}
    # two_obj ={}
    N_big = 10000
    Step_big = int((f2_max-f2_min)/N_big)
    Step_big = 1
    epsilon = f2_max - Step_big
    while epsilon > f2_min:
        Data.Total_dis_epsilon = epsilon
        best_obj, LB, Runtime, GAP, Gini, TT_time = Model(Data, Data.R)
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


def read_dic(Fname, All=False):
    if All:
        files = glob.glob(BASEDIR + f'/Data/Bi_Obj_results/*_2OBJ.txt')
    else:
        files = [BASEDIR+f'/Data/Bi_Obj_results/{Fname}_2OBJ.txt']

    two_objs = {}
    for myfile in files:
        Name = myfile.split("/")[-1].split(".")[0]
        with open(myfile, 'r') as file:
            two_objs[Name] =json.load(file)
        removed_key, _ = list(two_objs[Name].items())[0] # Remove the first element
        del two_objs[Name][removed_key]
        print(f"The removed key is {removed_key}")

    return two_objs


if __name__ == "__main__":
    BASEDIR = os.path.dirname(BASEDIR)
    Case_name = "Van"
    #Case_name = "Kartal"
    for NN in [30]: # [60,30,15]:
        Time = {15: 7200, 13: 7200, 30: 7200, 60: 7200}
        MaxTime = Time[NN]
        M = {60: 9, 30: 5, 15: 3, 13: 3}
        for inst in [20]:
            Data, File_name = utils.data_preparation(Case_name, NN, M[NN], inst)
            print(f"We are solving {File_name}")
            #two_obj = Epsilon_method(Data, UseModel2=True)
            #write_dic(File_name, two_obj)
            All_Two_objs = read_dic(File_name, All=True)
            for name in All_Two_objs:
                for ep, val in All_Two_objs[name].items():
                    print(f"Epsilon : {ep} -> Gini: {round(val[0], 2)} Total travel time : {val[1]} Solve Time : {round(val[2],2)}")
                plots.pareto_plot(name, All_Two_objs[name])
