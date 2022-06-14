import warnings

from utils import utils
import os
import glob
import sys

OWD = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def BnP_results_file(args):
    path = OWD + "/Data/updated_results"
    if len(args) >= 2:
        instance_type = args[1]
        if instance_type == "Van":
            file_names = glob.glob(path + f"/{instance_type}*[0-9]")
            if len(args) >= 3:
                instance_N = args[2]
                M = {60: 9, 30: 5, 15: 3, 13: 3}
                MM = M[int(instance_N)]
                file_names = glob.glob(path + f"/{instance_type}_{instance_N}_{MM}_*")
                if len(args) >= 4:
                    instance_index = args[3]
                    file_names = glob.glob(
                        path + f"/{instance_type}_{instance_N}_{MM}_{instance_index}")
        if instance_type == "Kartal":
            file_names = glob.glob(path + f"/{instance_type}*[0-9]")
            if len(args) >= 3:
                par_type = args[2]
                file_names = glob.glob(path + f"/{instance_type}_{par_type}_*")
                if len(args) >= 4:
                    instance_index = args[3]
                    file_names = glob.glob(
                        path + f"/{instance_type}_{par_type}_{instance_index}")
        if len(file_names) == 0:
            print("Incorrect input!!")
    else:
        file_names = glob.glob(path+"/Kartal_*")

    return file_names

def Model_results_file(args):
    path = OWD + "/Data"
    file_names =[]
    if len(args) >= 2:
        instance_type = args[1]
        if instance_type == "Van":
            file_names = glob.glob(path + f"/{instance_type}/{instance_type}_*_Model1_V2")
            if len(args) >= 3:
                instance_N = args[2]
                M = {60: 9, 30: 5, 15: 3, 13: 3}
                MM = M[int(instance_N)]
                file_names = glob.glob(path + f"/{instance_type}/{instance_type}_{instance_N}_{MM}_*_Model1_V2")
                if len(args) >= 4:
                    instance_index = args[3]
                    file_names = glob.glob(path + f"/{instance_type}/{instance_type}_{instance_N}_{MM}_{instance_index}_Model1_V2")
        if instance_type == "Kartal":
            file_names = glob.glob(path + f"/{instance_type}/{instance_type}_*_*_Model1_V2")
            if len(args) >= 3:
                par_type = args[2]
                file_names = glob.glob(path + f"/{instance_type}/{instance_type}_{par_type}_*_Model1_V2")
                if len(args) >= 4:
                    instance_index = args[3]
                    file_names = glob.glob(path + f"/{instance_type}/{instance_type}_{par_type}_{instance_index}_Model1_V2")
    else:
        file_names = glob.glob(path + "/Kartal/Kartal_T_7_Model1_V2")

    if len(file_names) == 0:
        print("Incorrect input!!")
        print_how2use()
    clean_names = [name for name in file_names if "_Model1_V2" in name]
    return clean_names


def print_how2use():
    print("First argument (mandatory) -> Model, BnP")
    print("Second argument (optional) -> Kartal(default), Van")
    print("Third argument (Optional) -> Number of nodes: 13, 15, 30, 60")
    print("Forth argumnet (Optional) -> Instance ID")


if __name__ == "__main__":

    if len(sys.argv) <= 1:
        warnings.warn("Use the command line to read the results")
        print_how2use()
        exit()
    if sys.argv[1] == "BnP" or len(sys.argv) < 2:
        file_names = BnP_results_file(sys.argv[1:])
    elif sys.argv[1] == "Model":
        file_names = Model_results_file(sys.argv[1:])

    for file_path in file_names:
        instance_name = file_path.split("/")[-1]
        result = utils.read_object(file_path)
        if isinstance(result, dict):
            for s in result:
                string = str(s) + "\t"
                string += "\t".join([str(round(a,3)) for a in result[s]])
                print(f"{string}")
        else:
            string = instance_name + "\t"
            string += "\t".join([str(a) for a in result])
            print(f"{string}")