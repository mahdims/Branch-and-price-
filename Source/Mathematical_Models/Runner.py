from time import time
from Model2 import Model2
from Model1_V2 import Model1_V2
from Model1 import Model1

import os
import sys
OWD = os.getcwd()
sys.path.insert(0,OWD+"/Source")
from utils import utils

if __name__ == "__main__":
    OWD = os.getcwd()
    # Case_name = "Van"
    Case_name="Kartal"
    NN = 13
    for NN in [13]: # [60,30,15]:
        Time = {15: 1000, 13: 1000, 30: 1800, 60: 3600}
        MaxTime = Time[NN]
        results = {}
        M = {60: 9, 30: 5, 15: 3, 13: 3}
        for inst in range(18, 19):
            Data, File_name = utils.data_preparation(Case_name, NN, M[NN], inst)
            print(f"We are solving {File_name}")
            start = time()
            # best_obj, LB, Runtime, GAP = Model1(Data, Data.R)
            best_obj, LB, Runtime, GAP = Model2(Data, Data.R)
            # best_obj, LB, Runtime, GAP = Model1_V2(Data, Data.R)

            print(f"The optimal objective is {best_obj}")
            results[File_name] = [best_obj, LB, Runtime, GAP]
            Model_runtime = time()-start

        
        # save_object(results,'G:\My Drive\\1-PhD thesis\\2 - equitable relief routing\Code\%s\%s_NewModel' %(Case_name,File_name) )
        
        # save_object(results,'G:\My Drive\\1-PhD thesis\\2 - equitable relief routing\Code\%s\%s_Modelresult' %(Case_name,File_name) )




