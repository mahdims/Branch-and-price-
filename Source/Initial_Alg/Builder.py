import copy
import itertools as it
from utils import Route_delivery as RD
from Initial_Alg.Solution import Solution
import random
import sys

def Gini(demands):
    gini = 0
    for d1, d2 in it.combinations(demands, 2):
        gini += abs(d1-d2)

    return gini/len(demands)


def assignment_cost(bins, bin_inx, item):
    demands = [sum([i.demand for i in b]) for b in bins]
    demands[bin_inx] += item.demand
    return Gini(demands)


def greedy_build(Data, dis, alpha, beta, flag="sorted"):
    All_seq = Data.All_seq
    unassigned = [item[0] for inx, item in All_seq.items() if inx != "D0" and inx != "D1"]
    if flag == "sorted":
        unassigned = sorted(unassigned, key=lambda x: x.demand, reverse=True)
    elif flag == "random":
        random.shuffle(unassigned)
    else:
        sys.exit("Wrong flag input for greedy_build function i Builder")
    bins = []
    for i in range(Data.M):
        bins.append([unassigned.pop(0)])

    for item in unassigned:
        best_cost = -1
        best_bin = None
        for bin_inx in range(len(bins)):
            cost = assignment_cost(bins, bin_inx, item)
            if best_cost == -1 or cost < best_cost:
                best_cost = cost
                best_bin = bin_inx
        bins[best_bin].append(item)

    routes = []

    for bin in bins:
        bin.insert(0, All_seq["D0"][0])
        bin += All_seq["D1"]
        new_RD = RD.RouteDel(bin)
        new_RD.calc_time(dis)
        routes.append(new_RD)

    new_sol = Solution(routes, alpha, beta)

    return new_sol


def combine_score(Data, dis, routes, r1, r2):
    i_r1 = routes[r1][-2]
    j_r2 = routes[r2][1]
    distance_save = dis[i_r1[-1], routes[r1][-1][0]] + dis[routes[r1][0][-1], j_r2[0]] - dis[i_r1[-1], j_r2[0]]

    feasible =0
    if routes[r1].travel_time + routes[r1].travel_time - distance_save <= Data.Maxtour:
        feasible = 1
    demands = [sum([i.demand for i in b]) for b in routes]
    Current_gini = Gini(demands)
    demands[r1] = demands[r1] + demands[r2]
    del demands[r2]
    gini = Gini(demands)
    gini = Current_gini - gini

    return feasible, distance_save, gini


def apply_the_merge(dis, routes, selected_move):
    r1 = selected_move[0]
    r2 = selected_move[1]
    start_inx = len(routes[r1]) - 2
    for sec in routes[r2][1:-1]:
        added_time = routes[r1].insertion_time(dis, start_inx, sec)
        routes[r1].insert(start_inx, sec, added_time)
        start_inx += 1

    del routes[r2]
    return routes


def CW(Data, dis, alpha, beta):
    All_seq = Data.All_seq
    routes = []
    for inx, item in All_seq.items():
        if inx != "D0" and inx != "D1":
            route = [All_seq["D0"][0]]
            route.append(item[0])
            route += All_seq["D1"]
            routes.append(RD.RouteDel(route))

    accepted_move = 1
    while accepted_move:
        candidate_list = []
        accepted_move = 0
        for r1, r2 in it.combinations(range(len(routes)), 2):
            feasible, distance, gini = combine_score(Data, dis, routes, r1, r2)
            if feasible and distance > 0:
                candidate_list.append([r1, r2, feasible, distance, gini, 0]) # convert the saving to cost by the minus

            feasible, distance, gini = combine_score(Data, dis, routes, r2, r1)
            if feasible  and distance > 0:
                candidate_list.append([r2, r1, feasible, distance, gini, 0])

        if len(candidate_list):
            max_gini = max(candidate_list, key=lambda x:x[4])[4]
            max_distance = max(candidate_list, key=lambda x:x[3])[3]
            for move in candidate_list:
                move[5] = move[3]/max_distance + move[4]/max_gini

            selected_move = max(candidate_list, key=lambda x: x[5])
            routes = apply_the_merge(dis, routes, selected_move)
            accepted_move = 1

    new_sol = Solution(routes, alpha, beta)
    return new_sol




