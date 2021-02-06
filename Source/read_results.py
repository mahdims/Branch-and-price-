from utils import utils
import os
import glob
OWD = os.getcwd()

path = OWD + "/Data/updated_results"
file_names = glob.glob(path+"/Van_30_5_14_?")
for file_path in file_names:
    instance_name = file_path.split("/")[-1]
    result = utils.read_object(file_path)
    string = ""
    for s in result:
        string += "\t" + str(round(s, 2))
    print(f"{instance_name} :{string}")