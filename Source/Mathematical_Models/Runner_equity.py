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


def write_dic(Fname,WE_WOUTE):
    try:
        old_dic = read_dic(Fname)[Fname]
        WE_WOUTE.update(old_dic)
    except:
        pass
    with open(BASEDIR+f'/Data/Equity_Price/{Fname}_EP.txt', 'w') as file:
        file.write(json.dumps(WE_WOUTE))


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


def read_dic(Fname="", All=False):
    if All:
        files = glob.glob(BASEDIR + f'/Data/Equity_Price/*_EP.txt')
    else:
        files = [BASEDIR+f'/Data/Equity_Price/{Fname}_EP.txt']

    two_objs = {}
    for myfile in files:
        Name = myfile.split("/")[-1].split(".")[0].replace("_cap", "")
        with open(myfile, 'r') as file:
            two_objs[Name] =json.load(file)
        # removed_key, _ = list(two_objs[Name].items())[0] # Remove the first element
        # del two_objs[Name][removed_key]
        # print(f"The removed key is {removed_key}")

    return two_objs


def calc_UnSatisfied_AbsGini(Data, IAAF, TT_slack, Giniindex):

    IAAF = IAAF + (Data.Gamma/Data.R) * TT_slack
    UD = IAAF / (1 + 2 * Data.Lambda * Giniindex)
    AbsGini = 2 * Data.total_demand * Giniindex * UD

    return UD, AbsGini


def print_sols_excel_style(File_name, All_sols):
    # sorted_keys = sorted(All_sols, key=lambda x: float(x), reverse=True)
    # best_obj, LB, Runtime, GAP, AbsGini, TT_time, GiniI, Total_unS

    for ep in All_sols:
        val = All_sols[ep]
        print(f"{File_name} \t {ep}\t" + f"\t".join([str(round(a, 3)).ljust(10) for a in val]))


def new_names(name, case_name, inst_type, inst):
    if case_name == "Van":
        inst = inst % 5
        if inst ==0: inst = 5
        seps = name.split("_")
        new_name = seps[0] + seps[1]
        new_name += f"_{inst_type}{inst}"
    else:
        seps = name.split("_")
        new_name = f"{seps[0]}_{seps[1]}{seps[2]}"
    return new_name


if __name__ == "__main__":
    BASEDIR = os.path.dirname(BASEDIR)
    All_sols = {}
    Case_name = "Van"
    #Case_name = "Kartal"
    All_nondominat = {"A": [], "T": [], "VT": [], "VTL": []}
    nonD_sols_Full_info = []

    # Time = {15: 7200, 13: 7200, 30: 7200, 60: 7200}
    # MaxTime = Time[NN]
    Instances_sel = {("Van", 15): [16, 3, 5, 10, 11], ("Van", 30): [20, 1, 2, 10, 13], ("Van", 60): [5, 17],
                 ("Kartal", 13): [3, 6, 17, 25, 32]}
    Instances = {("Van", 15): range(1,20), ("Van", 30): range(1,20), ("Van", 60): range(1,20),
                 ("Kartal", 13): range(1,40)}
    # Instances_4_plotting = {("Van", 15): [11], ("Van", 30): [10], ("Van", 60): [2],
    #             ("Kartal", 13): [25]}
    # Instances_4_plottingCap = {("Van", 15): [11], ("Kartal", 13): [17], ("Van", 30): [1]}
    '''
    for (Case_name, NN), vals in Instances.items():
        M = {60: 9, 30: 5, 15: 3, 13: 3}
        for inst in vals:
            Data, File_name, ins_type = utils.data_preparation(Case_name, NN, M[NN], inst)
            print(f"We are solving {File_name}")

            All_sols[File_name]= {}
            Data.Lambda = 0
            Data.Alpha = 1
            best_obj, LB, Runtime, GAP, AbsGini, TT_time, GiniI, Total_unS = Model2(Data, Data.R)
            All_sols[File_name]["Only_UNS"] = [best_obj, LB, Runtime, GAP, AbsGini, TT_time, GiniI, Total_unS]

            Data.Lambda = 1
            Data.Alpha = 0
            best_obj, LB, Runtime, GAP, AbsGini, TT_time, GiniI, Total_unS = Model2(Data, Data.R)
            All_sols[File_name]["Only_Equity"] = [best_obj, LB, Runtime, GAP, AbsGini, TT_time, GiniI, Total_unS]

            Data.Lambda = 0.5
            Data.Alpha = 1
            best_obj, LB, Runtime, GAP, AbsGini, TT_time, GiniI, Total_unS = Model2(Data, Data.R)
            All_sols[File_name]["IAAF"] = [best_obj, LB, Runtime, GAP, AbsGini, TT_time, GiniI, Total_unS]


            write_dic(File_name, All_sols[File_name])
    '''
    print(
        f"Instance \t objective \t IAAF \t LB \t Time \t Gap \t AbsGini \t Route Length \t Gini index \t Total Unsatisfied")
    All_sols = read_dic(All=True)
    for Fname in All_sols.keys():
        print_sols_excel_style(Fname, All_sols[Fname])
        # plots.capacity_plot(new_names(Fname, Case_name, ins_type, inst), All_sols[Fname])
        # '''