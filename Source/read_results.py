from utils import utils
import os
import glob
import sys

OWD = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

path = OWD + "/Data/updated_results"

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        instance_type = sys.argv[1]
        file_names = glob.glob(path + f"/{instance_type}*[0-9]")
        if len(sys.argv) >= 3:
            instance_N = sys.argv[2]
            M = {60: 9, 30: 5, 15: 3, 13: 3}
            MM = M[int(instance_N)]
            file_names = glob.glob(path + f"/{instance_type}_{instance_N}_{MM}_*[0-9]")
            if len(sys.argv) >= 4:
                instance_index = sys.argv[3]
                file_names = glob.glob(path + f"/{instance_type}_{instance_N}_{MM}_{instance_index}")
        if len(file_names) == 0:
            print("Incorrect input!!")
    else:
        file_names = glob.glob(path+"/Van_30_5_*")

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
            string += "\t".join([str(round(a,3)) for a in result])
            print(f"{string}")