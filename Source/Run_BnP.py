import os
from BnP import BnP
from utils import utils


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

    for NN in [30]:  # [60,30,15]:
        Time = {15: 7200, 13: 7200, 30: 7200, 60: 7200}
        MaxTime = Time[NN]
        M = {60: 9, 30: 5, 15: 3, 13: 3}
        for inst in [14, 15]: #[22, 24, 29, 30]:# range(1,10):
            Data, File_name = utils.data_preparation(Case_name, NN, M[NN], inst)
            Data = utils.set_parameters(Data)
            # TEST
            # Data.M = 5
            # MQ = Data.M * Data.Q
            # Supply = Data.G.nodes[0]["supply"]
            # Data.Q = 20000
            # END TEST

            print(f"We are solving {File_name}")
            results = BnP.branch_and_bound(Data, MaxTime, File_name)
            print("\t".join(results))
            save_the_results([File_name] + list(results))
            # utils.print_the_solution(Bsolution)
            utils.save_object(results, BaseDir + f"/Data/updated_results/{File_name}")
            # save_object(results,'.\%s\%s_BnPresult' %(Case_name,File_name))
    # save_object(R, "TObj_R_Kartal" )

