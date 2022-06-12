from time import time
from Model2 import Model2
from Model1_V2 import Model1_V2
from Model1 import Model1
import os
import sys
BASEDIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, BASEDIR)
from utils import utils

if __name__ == "__main__":
    BASEDIR = os.path.dirname(BASEDIR)
    Case_name = "Van"
    #Case_name="Kartal"
    NN = 13
    for NN in [15]: # [60,30,15]:
        Time = {15: 1000, 13: 1000, 30: 1800, 60: 3600}
        MaxTime = Time[NN]
        results = {}
        M = {60: 9, 30: 5, 15: 3, 13: 3}
        for inst in [16]:
            Data, File_name = utils.data_preparation(Case_name, NN, M[NN], inst)
            print(f"We are solving {File_name}")

            start = time()
            # best_obj, LB, Runtime, GAP = Model1(Data, Data.R)
            # best_obj, LB, Runtime, GAP = Model2(Data, Data.R)
            best_obj, LB, Runtime, GAP, _, _ = Model1_V2(Data, Data.R, SecondObjOnly=False)
            print(f"The optimal objective is {best_obj}")
            results[File_name] = [best_obj, LB, Runtime, GAP]
            Model_runtime = time()-start

            utils.save_object(results, BASEDIR+'/Data/%s/%s_Model1_V2' %(Case_name, File_name))

