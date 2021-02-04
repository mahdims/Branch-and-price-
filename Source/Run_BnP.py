import time
import os
from BnP import BnP
import numpy as np
import math
from utils import utils


def test_the_distance_symmetry(Dis):
    for i,j in Dis.keys():
        if i<j :
            if Dis[i,j] != Dis[j,i]:
                print("Not symmetrical distances")
                break


def data_preparation(Case_name, NN, M, inst):

    if Case_name == "Van":
        if inst <= 5:
            ins_type = "T"
        elif inst <= 10:
            ins_type = "VT"
        else:
            ins_type = "VTL"
        File_name = '%s_%d_%d_%d' % (Case_name, NN, M, inst)
        R_dic = utils.read_object(f"./Data/{Case_name}/TObj_R_Van{NN}")

    elif Case_name == "Kartal":
        if inst <= 10:
            ins_type = "T"
        elif inst <= 20:
            ins_type = "VT"
            inst -= 10
        else:
            ins_type = "VTL"
            inst -= 20
        File_name = '%s_%s_%d' % (Case_name, ins_type, inst)
        R_dic = utils.read_object("./TObj_R_Kartal")

    Data = utils.read_object(f'./Data/{Case_name}/{File_name}')
    R = R_dic[File_name]
    Data.R = R

    # If the distance are symmetric
    # test_the_distance_symmetry(Data.distances)
    # please make sure that this won't effect anything (Making the i,NN+1 arc zero )
    for i in range(NN):
        Data.distances[i, NN + 1] = 0

    if Case_name == "Van":
        Data.Gamma = 0.1
    elif Case_name == "Kartal":
        Data.Gamma = 1

    # Data.Lambda = 0
    zeta1 = 2
    if ins_type == "T":
        zeta2 = 0.5
    if ins_type == "VT":
        zeta2 = 0.2
    if ins_type == "VTL":
        zeta2 = 0.2
        zeta1 = 1

    Data.Maxtour = zeta1 * math.ceil(float(NN) / M) * np.percentile(list(Data.distances.values()), 50)
    Data.Q = zeta2 * Data.G.nodes[0]['supply'] / M
    Data.Total_dis_epsilon = 0.85 * M * Data.Maxtour

    return Data, File_name


if __name__ == "__main__":
    OWD = os.getcwd()
    Case_name = "Van"
    # Case_name="Kartal"
    NN = 13
    for NN in [30]: # [60,30,15]:
        Time = {15: 1000, 13: 1000, 30: 1800, 60: 3600}
        MaxTime = Time[NN]
        results = {}
        M = {60: 9, 30: 5, 15: 3, 13: 3}
        for inst in range(5, 13):
            Data, File_name = data_preparation(Case_name, NN, M[NN], inst)
            Avg_results = []
            for ID in [1, 2]:
                print(f"We are solving {File_name}_{ID}")
                try:
                    UB, LB, Gap, time2UB, Elapsed_time = BnP.branch_and_bound(Data, MaxTime, File_name+"_"+str(ID))
                except :
                    [UB, LB, Gap, time2UB, Elapsed_time] = utils.read_object(OWD + f"/Data/updated_results/{File_name}_{ID}")

                Avg_results.append([UB, LB, Gap, time2UB, Elapsed_time])

            results[File_name] = min(Avg_results, key=lambda x:x[0])

            # print_the_solution(Bsolution)
            utils.save_object(results, OWD + f"/Data/updated_results/{File_name}")
            #save_object(results,'G:\My Drive\\1-PhD thesis\equitable relief routing\Code\%s\%s_BnPresult' %(Case_name,File_name) )
    #save_object(R, "TObj_R_Kartal" )