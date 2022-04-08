import os
from BnP import BnP
from utils import utils


def test_the_distance_symmetry(Dis):
    for i, j in Dis.keys():
        if i < j:
            if Dis[i, j] != Dis[j, i]:
                print("Not symmetrical distances")
                break


if __name__ == "__main__":
    OWD = os.getcwd()
    # Case_name = "Van"
    Case_name = "Kartal"

    for NN in [13]: # [60,30,15]:
        Time = {15: 1000, 13: 1000, 30: 1800, 60: 3600}
        MaxTime = Time[NN]
        results = {}
        M = {60: 9, 30: 5, 15: 3, 13: 3}
        for inst in [14]:
            Data, File_name = utils.data_preparation(Case_name, NN, M[NN], inst)

            # TEST
            # Data.M = 4
            # MQ = Data.M * Data.Q

            # Supply = Data.G.nodes[0]["supply"]
            # Data.Q = 10000
            # END TEST
            Avg_results = []
            for ID in [1]:
                print(f"We are solving {File_name}")
                # try:
                UB, LB, Gap, time2UB, Elapsed_time = BnP.branch_and_bound(Data, MaxTime, File_name+"_"+str(ID))
                # except :
                # [UB, LB, Gap, time2UB, Elapsed_time] =
                # utils.read_object(OWD + f"/Data/updated_results/{File_name}_{ID}")
                Avg_results.append([UB, LB, Gap, time2UB, Elapsed_time])

            results[File_name] = min(Avg_results, key=lambda x:x[0])

            # utils.print_the_solution(Bsolution)
            # utils.save_object(results, OWD + f"/Data/updated_results/{File_name}")
            # save_object(results,'.\%s\%s_BnPresult' %(Case_name,File_name))
    # save_object(R, "TObj_R_Kartal" )

