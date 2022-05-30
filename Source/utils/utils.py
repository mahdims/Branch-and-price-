import sys
import numpy as np
import math
import pickle5 as Pick
import random as rand
import itertools as it
from os import path
from datetime import datetime
from utils import Route_delivery as RD


def demand_proportional(Data, route_del):

    for key, val in route_del.RDP.items():
        route_d = 0
        ratio = 0
        for n in range(1, Data.NN):
            n_demand = Data.G.nodes[n]["demand"]
            route_d += n_demand * (int(val[n]) != 0)
            new_ratio = round(val[n]/n_demand, 3)
            if new_ratio != 0:
                if ratio == 0:
                    ratio = new_ratio
                elif ratio != new_ratio:
                    print(f"Not demand proportional {route_del.creator}")
                    #sys.exit("The new valid inequality is not respected")

        total_del = round(sum(val),0)
        if route_d * Data.C > Data.Q:
            if total_del != Data.Q:
                print(f"Not equal to Q {route_del.creator}")
                sys.exit("The new valid inequality is not respected")
        else:
            if total_del < route_d * Data.C:
                print(f"Not bigger than D/C {route_del.creator}")
                sys.exit("The new valid inequality is not respected")
    return 1



def calculate_the_obj(Data, Routes, RDPs):
    Gc = Data.Gc
    # create the mapping to find the node quantities  :))
    Q_mapping = {}
    for i in Gc.nodes:
        for r_ID, route in enumerate(Routes):
            if route.is_visit(i) != -1:
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
        if route.is_visit(i) != -1 and route.is_visit(j) != -1:
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
            if route.is_visit(j) != -1:
                return 1
        elif seq[0] == j:
            if route.is_visit(i) != -1:
                return 1
    return 0


def keep_NR_check(route, seq, keeps):
    # Checks if seq can be in this route and return 1 if there is a violation
    for i, j in keeps:
        if seq[0] == i:
            if not route.is_visit(j) != -1:
                return 1

        if seq[0] == j:
            if not route.is_visit(i) != -1:
                return 1

    return 0


def avoid_check(route, avoids, seq=[], i=-1):
    # Returns the list of violated avoids
    out = []
    if isinstance(seq, list):
        for i, j in avoids:
            index_i = route.is_visit(i)
            if index_i != -1:
                per_inx = index_i - 1
                if per_inx >= 0:
                    if j == route.nodes_in_path[per_inx]:
                        out.append((i, j))

                next_inx = index_i + 1
                if next_inx < len(route.nodes_in_path):
                    if j == route.nodes_in_path[next_inx]:
                        out.append((i, j))
    else:
        out = {"Add": [], "Remove": []}
        removed_n1, removed_n2 = (route[i][-1], route[i + 1][0])
        if (removed_n1, removed_n2) in avoids:
            out["Remove"].append((removed_n1, removed_n2))
        elif (removed_n2, removed_n1) in avoids:
            out["Remove"].append((removed_n2, removed_n1))

        new_edges = [(route[i][-1], seq[0]),  (seq[-1], route[i + 1][0])]
        for a, b in new_edges:
            if (a, b) in avoids:
                out["Add"].append((a, b))
            elif (b, a) in avoids:
                out["Add"].append((b, a))
            else:
                pass
    return out


def keep_check(route, keeps, seq=[], i=-1):
    # Return a list of avoided keeps
    out = []
    if isinstance(seq, list):
        for i, j in keeps:
            i_inx = route.is_visit(i)
            j_inx = route.is_visit(j)
            if i_inx != -1 and j_inx != -1:
                if (i_inx+1) == j_inx or (j_inx+1) == i_inx:
                    pass
                else:
                    out.append((i, j))
            elif i_inx == -1 and j_inx == -1:
                pass
            else:
                out.append((i, j))
    else:
        # the added violated keeps and the removed violated keeps
        out = {"Add": [], "Remove": []}
        removed_n1, removed_n2 = (route[i][-1], route[i + 1][0])

        if (removed_n1, removed_n2) in keeps:
            out["Add"].append((removed_n1, removed_n2))
        elif (removed_n2, removed_n1) in keeps:
            out["Add"].append((removed_n2, removed_n1))

        new_edges = [(route[i][-1], seq[0]), (seq[-1], route[i + 1][0])]

        for a, b in keeps:
            for n1, n2 in new_edges:
                if (a == n1 and b == n2) or (a == n2 and b == n1):
                    out["Remove"].append((a, b))

    return out


def check_branching(Data, col_dic, avoid, keep):

    if avoid:
        # print("Start check the list of edges to avoid")
        # print(avoid)
        for name, r in col_dic.items():
            if len(avoid_check(r, avoid)) != 0:
                print(r)
                print(f"The RD index {name} out of {len(col_dic)} created with {r.creator}")
                print(keep)
                sys.exit(f"Avoided is not correct!!! {avoid}")

    if keep:
        # print("Start checking the keep edges")
        # print(keep)
        for name, r in col_dic.items():
            if len(keep_check(r, keep)) != 0:
                print(r)
                print(f"The RD index {name} out of {len(col_dic)} created with {r.creator}")
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
    New_Route = RD.RouteDel(seq_route, "MIP")
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


def set_parameters(Data):

    Data.IMP_frequency = 1
    Data.N_Added_GRASP = 10
    return Data


def data_preparation(Case_name, NN, M, inst):
    BASE_DIR = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
    if Case_name == "Van":
        if inst <= 5:
            ins_type = "T"
        elif inst <= 10:
            ins_type = "VT"
        elif inst <= 15:
            ins_type = "VTL"
        else:
            ins_type = "A"

        File_name = '%s_%d_%d_%d' % (Case_name, NN, M, inst)
        R_dic = read_object(f"{BASE_DIR}/Data/{Case_name}/TObj_R_Van{NN}")

    elif Case_name == "Kartal":
        if inst <= 10:
            ins_type = "T"
        elif inst <= 20:
            ins_type = "VT"
            inst -= 10
        elif inst <= 30:
            ins_type = "VTL"
            inst -= 20
        else:
            ins_type = "A"
            inst -= 30
        File_name = '%s_%s_%d' % (Case_name, ins_type, inst)
        R_dic = read_object(f"{BASE_DIR}/Data/{Case_name}/TObj_R_Kartal")

    Data = read_object(f'{BASE_DIR}/Data/{Case_name}/{File_name}')
    if ins_type == "A":
        R = 500
    else:
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
    if ins_type == "A":
        zeta2 = 1.2
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

    # make sure there is no shelter with zero demand
    for n in Data.G.nodes():
        if Data.G.nodes[n]["demand"] == 0 and n != 0 and n != Data.NN+1:
            Data.G.nodes[n]["demand"] = 10
            Data.Gc.nodes[n]["demand"] = 10
            Data.total_demand += 10

    return Data, File_name


def write_log(results, path_2_file, Routes=[], RDPs=[]):
    now_today = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    content = [str(round(a, 3))+" " for a in results]
    content = "**"*5 + f"{now_today}" + "**"*5 + "\n" + "".join(content)+"\r\n"
    f = open(path_2_file, "a+")
    f.write(content)
    for inx, r in enumerate(Routes):
        f.write(" ".join([str(0)] + [str(a) for a in r.nodes_in_path]) + "\n")
        if len(RDPs) != 0:
            f.write(" ".join([str(round(a,1)) for a in RDPs[inx]]) + "\n")
    f.close()


def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)


def read_object(filename):
    with open(filename, 'rb') as input:
        obj = Pick.load(input, encoding='latin1')
    return obj
