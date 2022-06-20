"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""

import os
from BnP import BnP, Node
from utils import utils, plots


def test_the_distance_symmetry(Dis):
    for i, j in Dis.keys():
        if i < j:
            if Dis[i, j] != Dis[j, i]:
                print("Not symmetrical distances")
                break


def save_the_results(res):
    BaseDir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    myfile = open(BaseDir + "/Data/Results/LOG.txt", "a+")
    myfile.write("\t".join(res) + "\r\n")
    myfile.close()


if __name__ == "__main__":
    BaseDir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    Case_name = "Van"
    #Case_name = "Kartal"
    two_objs = {}
    for NN in [15]:  # [60,30,15]:
        Time = {15: 1000, 13: 1000, 30: 1800, 60: 3600}
        MaxTime = Time[NN]
        M = {60: 9, 30: 5, 15: 3, 13: 3}
        for inst in [16]: #[8, 9, 10]: # range(11,12):
            Data, File_name = utils.data_preparation(Case_name, NN, M[NN], inst)
            Data = utils.set_parameters(Data)
            for epsilon in [22000]: # [30000, 24000, 23000, 22800, 22500, 22400, 22300, 22200, 22100, 21812]:
                Data.Total_dis_epsilon = epsilon

                print(f"We are solving {File_name}")

                results = BnP.branch_and_bound(Data, MaxTime, File_name)
                print("\t".join(results))
                two_objs[epsilon] = (Node.Node.abs_Gini, Node.Node.Total_time)
                print(f"The maximum allowed travel time {Data.Total_dis_epsilon}"
                      f"\nThe total travelling time: {Node.Node.Total_time}")
                print(f"The Absolute Gini {Node.Node.abs_Gini}")
                #save_the_results([File_name] + list(results))
                Node.Node.reset()
                # utils.print_the_solution(Bsolution)
                # utils.save_object(results, BaseDir + f"/Data/updated_results/{File_name}")
        plots.pareto_plot(two_objs)

