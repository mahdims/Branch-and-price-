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

    _, _, Runtime1, _, f1_max, f2_min, GiniI1 = Model(Data, Data.R, SecondObjOnly=True)
    _, _, Runtime2, _, f1_min, f2_max, GiniI2 = Model(Data, Data.R, FirstObjOnly=True)
    two_obj = {f2_max: [f1_min, f2_max, Runtime2, GiniI2], f2_min: [f1_max, f2_min,Runtime1, GiniI1]}
    # two_obj ={}
    N_big = 10000
    Step_big = 1
    epsilon = f2_max - Step_big
    while epsilon > f2_min:
        Data.Total_dis_epsilon = epsilon
        best_obj, LB, Runtime, GAP, AbsGini, TT_time, GiniI = Model(Data, Data.R)
        print(f"The optimal objective is {best_obj}, IAAF: {AbsGini}, Gini Index: {GiniI} TT: {TT_time}")
        two_obj[epsilon] = [AbsGini, TT_time, Runtime, GiniI]

        if TT_time < epsilon - Step_big:
            epsilon = TT_time - Step_big
        else:
            epsilon = epsilon - Step_big

    return two_obj


def write_dic(Fname,two_obj):

    with open(BASEDIR+f'/Data/Bi_Obj_results/{Fname}_2OBJ.txt', 'w') as file:
        file.write(json.dumps(two_obj))


def non_dominant_sols(TwoObj):
    current_f1 = 0
    NonDominat = []
    TwoObj_sorted = sorted(TwoObj.items(), key=lambda x:x[1][1], reverse=True)
    current_f2 = TwoObj_sorted[0][1][1]
    current_f1 = TwoObj_sorted[0][1][0]
    NonDominat.append(TwoObj_sorted[0][1])

    for key, sol in TwoObj_sorted[1:]:
        if round(float(sol[0]), 3) > round(current_f1, 3):
            current_f1 = float(sol[0])
            NonDominat.append(sol)
        else:
            dominated = []
            for inx, old_sol in enumerate(NonDominat):
                if round(float(sol[0]), 3) <= round(float(old_sol[0]), 3):
                    dominated.append(inx)
            while dominated:
                inx = dominated.pop()
                if len(dominated) == 0:
                    NonDominat[inx] = sol
                else:
                    del NonDominat[inx]

    return NonDominat


def read_dic(Fname, All=False):
    if All:
        files = glob.glob(BASEDIR + f'/Data/Bi_Obj_results/*_2OBJ.txt')
    else:
        files = [BASEDIR+f'/Data/Bi_Obj_results/{Fname}_2OBJ.txt']

    two_objs = {}
    for myfile in files:
        Name = myfile.split("/")[-1].split(".")[0].replace("_2OBJ", "")
        with open(myfile, 'r') as file:
            two_objs[Name] =json.load(file)
        #removed_key, _ = list(two_objs[Name].items())[0] # Remove the first element
        #del two_objs[Name][removed_key]
        # print(f"The removed key is {removed_key}")

    return two_objs


def calc_UnSatisfied_AbsGini(Data, IAAF, TT_slack, Giniindex):

    IAAF = IAAF + (Data.Gamma/Data.R) * TT_slack
    UD = IAAF / (1 + 2 * Data.Lambda * Giniindex)
    AbsGini = 2 * Data.total_demand * Giniindex * UD

    return UD, AbsGini


def print_sols_excel_style(Two_objs):
    sorted_keys = sorted(Two_objs, reverse=True)

    Short_RL = min(non_dominants, key=lambda x: x[1])
    print(f"\t\tIAAF \t Route Length \tTime \t Gini index\t  Total UD\t AbsGini \t RL increase%\t IAAF decrease")
    for ep in sorted_keys:
        val = Two_objs[ep]
        if len(val) >= 4:
            f2_increase = -1
            f1_decrease = -1
            if val in non_dominants:
                f2_increase = (val[1] - Short_RL[1]) * 100 / Short_RL[1]
                f1_decrease = (Short_RL[0] - val[0]) * 100 / Short_RL[0]

            UnDemand, absGini = calc_UnSatisfied_AbsGini(Data, val[0], float(ep) - val[1], val[3])
            print(str(val in non_dominants) + "\t" + f"\t".join(
                [str(round(a, 3)).ljust(10) for a in val]) +
                  f"\t{round(UnDemand)}\t{round(absGini)}\t{round(f2_increase,4):<10}{round(f1_decrease,4):<10}")

        else:
            print(f"Instance with no Gini Index information {Fname}")


if __name__ == "__main__":
    BASEDIR = os.path.dirname(BASEDIR)
    All_Two_objs = {}
    Case_name = "Van"
    # Case_name = "Kartal"
    for NN in [15,30,60]: # [60,30,15]:
        Time = {15: 7200, 13: 7200, 30: 7200, 60: 7200}
        MaxTime = Time[NN]
        M = {60: 9, 30: 5, 15: 3, 13: 3}
        Instances = {("Van", 15): [16, 3, 5, 10, 11], ("Van", 30): [20, 1, 2, 10, 13], ("Van", 60): [2, 5, 6, 11, 17],
                     ("Kartal", 13): [3, 6, 17, 25, 32]}

        for inst in Instances[(Case_name, NN)]:
            Data, File_name = utils.data_preparation(Case_name, NN, M[NN], inst)
            # print(f"We are solving {File_name}")
            # All_Two_objs[File_name] = Epsilon_method(Data, UseModel2=True)
            # write_dic(File_name, All_Two_objs[File_name])
            All_Two_objs = read_dic(File_name, All=False)
            for Fname in All_Two_objs.keys():
                non_dominants = non_dominant_sols(All_Two_objs[Fname])
                TTime = sum([val[2] for val in All_Two_objs[Fname].values()])
                print(f"Name \t \t #Solved \t #Nondominant \t Time")
                print(f"{Fname:<15} {len(All_Two_objs[Fname]):<10} {len(non_dominants):<10} {round(TTime,3):<10}")
                print_sols_excel_style(All_Two_objs[Fname])
                #plots.pareto_plot(Fname, All_Two_objs[Fname], nondominant=non_dominants)

