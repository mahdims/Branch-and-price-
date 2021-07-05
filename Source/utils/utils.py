import sys
import numpy as np
import math
import pickle as Pick
import random as rand
import itertools as it
# import Real_Input
from utils import Route_delivery as RD


def calculate_the_obj(Data, Routes, RDPs):
    Gc = Data.Gc
    # create the mapping to find the node quantities  :))
    Q_mapping = {}
    for i in Gc.nodes:
        for r_ID, route in enumerate(Routes):
            if route.is_visit(i):
                break
        Q_mapping[i] = (r_ID, i)

    part1 = 0
    for i in Gc.nodes:
        (r_ID, inx) = Q_mapping[i]
        part1 += Gc.nodes[i]['demand'] - RDPs[r_ID][inx]

    part2 = 0
    for i, j in it.product(Gc.nodes, Gc.nodes):
        (r_IDi, inxi) = Q_mapping[i]
        (r_IDj, inxj) = Q_mapping[j]
        part2 += abs(Gc.nodes[j]['demand']*RDPs[r_IDi][inxi] - Gc.nodes[i]['demand']*RDPs[r_IDj][inxj])

    part2 = (Data.Lambda / Data.total_demand) * part2
    part3 = 0
    # part3 = Data.Gamma * (Data.Total_dis_epsilon - sum([r.travel_time for r in Routes])) / Data.R

    return part1+part2+part3


def edge_in_route(edge, route):

    # this function will check if route use edge i-j or not
    for i, j in [edge, (edge[1], edge[0])]:
        if route.is_visit(i) and route.is_visit(j):
            I_inx = route.where(i)
            if j in route[I_inx].string:
                return 1
            if route[I_inx][-1] == i and route[I_inx+1][0] == j:
                return 1

    return 0


def avoid_NR_check(route, seq, avoids):
    # This function checks if seq can be placed in the route considering the avoid
    # Return 1 if there is a violation (OW 0)
    for i, j in avoids:
        if seq[0] == i:
            if route.is_visit(j):
                return 1
        elif seq[0] == j:
            if route.is_visit(i):
                return 1
    return 0


def keep_NR_check(route, seq, keeps):
    # Checks if seq can be in this route and return 1 if there is a violation
    for i, j in keeps:
        if seq[0] == i:
            if not route.is_visit(j):
                return 1

        if seq[0] == j:
            if not route.is_visit(i):
                return 1

    return 0


def avoid_check(route, avoids):

    for i, j in avoids:
        if route.is_visit(i) and route.is_visit(j):
            # print(f"Two nodes {i, j} should be avoided but its here \n {route.nodes_in_path}")
            return 0

    return 1


def keep_check(route, keeps):

    for i, j in keeps:
        if route.is_visit(i) or route.is_visit(j):
            if route.is_visit(i) and route.is_visit(j):
                continue
            else:
                # print(f"nodes {(i, j)} are not together in the route \n {route.nodes_in_path}")
                return 0

    return 1


def check_branching(Data, col_dic, avoid, keep):

    if avoid:
        # print("Start check the list of edges to avoid")
        # print(avoid)
        for r in col_dic.values():
            if not avoid_check(r, avoid):
                print(r)
                sys.exit(f"Avoided is not correct!!! {avoid}")

    if keep:
        # print("Start checking the keep edges")
        # print(keep)
        for r in col_dic.values():
            if not keep_check(r, keep):
                print(r)
                sys.exit(f"Keep is not correct!!! {keep}")

    for r in col_dic.values():
        r.feasibility_check(Data)
        if not r.time_F:
            print(f"The following route is time infeasible {r.travel_time}")
            sys.exit(r)


def build_the_route(Data, Edges=[], route=[]):
    if Edges:
        PerNode = 0
        route = [0]
        while Edges:
            for e in Edges:
                if PerNode in e:
                    break
            route.append(e[1])
            PerNode = e[1]
            Edges.remove(e)

    if 0 not in route:
        route.insert(0, 0)
        route.append(0)

    seq_route = [Data.All_seq["D0"][-1]]
    if len(Data.All_seq["D0"]) > 1:
        for seq in Data.All_seq["D0"]:
            if route[1] in seq.string:
                seq_route = [seq]

    for node in route[1:-1]:
        if node in seq_route[-1].string:
            continue
        else:
            for key, seq in Data.All_seq.items():
                if isinstance(key, int): 
                    key = [key]
                if node in list(key):
                    if len(seq) > 1:
                        if node == seq[0][0]:
                            seq_route.append(seq[0])
                        else:
                            seq_route.append(seq[1])
                    else:
                        seq_route.append(seq[0])
                    break
    seq_route.append(Data.All_seq["D1"][0])
    New_Route = RD.RouteDel(seq_route)
    if 0 in New_Route.nodes_in_path:
        sys.exit("Find you")
    if route[1:-1] != New_Route.nodes_in_path:
        print("The build route function in column gen is not working correctly")
        print(New_Route.nodes_in_path)
        print(route[1:-1])
    return New_Route, route


def spin(rw):
    slot_count = len(rw)
    randno = rand.randint(0, 10000)
    rot_degree = randno % 360
    rot_unit = 360 / slot_count
    rol_no = (rot_degree - (rot_degree % (rot_unit))) / rot_unit
    rol_value = rw[int(rol_no)]
    return rol_value


def roul_wheel(dic):

    TotalVal = sum(dic.values())
    new_dic = {key: int(100 * val / TotalVal) for key, val in dic.items()}
    slot_count = sum(new_dic.values())

    roulette_wheel = [0] * slot_count
    for key, val in new_dic.items():
        j = 0
        while j < val:
            t = rand.randint(0, slot_count - 1)
            wheel_alloc = roulette_wheel[t]
            if wheel_alloc == 0:
                roulette_wheel[t] = key
                j = j + 1

    return spin(roulette_wheel)


def data_preparation(Case_name, NN, M, inst):

    if Case_name == "Van":
        if inst <= 5:
            ins_type = "T"
        elif inst <= 10:
            ins_type = "VT"
        else:
            ins_type = "VTL"
        File_name = '%s_%d_%d_%d' % (Case_name, NN, M, inst)
        R_dic = read_object(f"./Data/{Case_name}/TObj_R_Van{NN}")

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
        R_dic = read_object(f"./Data/{Case_name}/TObj_R_Kartal")

    Data = read_object(f'./Data/{Case_name}/{File_name}')
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

    Data.Maxtour = int(zeta1 * math.ceil(float(NN) / M) * np.percentile(list(Data.distances.values()), 50))
    Data.Q = int(zeta2 * Data.G.nodes[0]['supply'] / M)
    Data.Total_dis_epsilon = int(0.85 * M * Data.Maxtour)

    return Data, File_name


def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)


def read_object(filename):
    with open(filename, 'rb') as input:
        obj = Pick.load(input, encoding='latin1')
    return obj
