import itertools as it
from utils import Route_delivery as RD
from Initial_Alg.Solution import Solution
import random
import sys

def Gini(demands):
    gini = 0
    for d1, d2 in it.combinations(demands, 2 ):
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
        best_cost = 0
        best_bin = None
        for bin_inx in range(len(bins)):
            cost = assignment_cost(bins, bin_inx, item)
            if best_cost == 0 or cost < best_cost:
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