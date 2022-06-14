"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""

import numpy as np
import sys
# from Other_TSP_solvers import TSP_model, TSP_concorde, LKH3

# from Other_TSP_solvers import LKH3

def nearest_neighbor(dist_matrix, nodes, start=None):
    # Create a customer sequence by Nearest Neighbor algorithm
    # If  the start is given then the first node in the sequence would be start /
    # otherwise the function selects the first node in the sequence randomly.
    if start:
        path = [start]
        nodes.remove(start)
    else:
        inx = np.random.randint(len(nodes))
        path = [nodes.pop(inx)]

    while nodes:
        inx = dist_matrix[path[-1]][nodes].argmin()
        path.append(nodes.pop(inx))

    return path


def calc_path_dist(dist_matrix, path):
    path_distance = dist_matrix[path[-1]][path[0]]
    for ind in range(len(path) - 1):
        path_distance += dist_matrix[path[ind]][path[ind + 1]]
    return path_distance


def swap(path, swap_first, swap_last):
    path_updated = path[0:swap_first+1] + path[swap_last:-len(path) + swap_first:-1] \
                   + path[swap_last + 1:len(path)]
    return path_updated


def calc_distance_difference(dist_matrix, path, swap_first, swap_last):

    del_dist = dist_matrix[path[swap_first]][path[swap_first+1]] \
               + dist_matrix[path[swap_last]][path[swap_last+1]]
    add_dis = dist_matrix[path[swap_first]][path[swap_last]] \
              + dist_matrix[path[swap_first + 1]][path[swap_last + 1]]

    node = swap_first + 1
    while node != swap_last:
        del_dist += dist_matrix[path[node]][path[node + 1]]
        node += 1

    node = swap_last
    while node != swap_first + 1:
        add_dis += dist_matrix[path[node]][path[node-1]]
        node -= 1

    return add_dis - del_dist


def two_opt_Alg(dist_matrix, Nodes, start=None):
    # This is the 2-opt algorithm
    N = len(Nodes)
    best_route = nearest_neighbor(dist_matrix, list(Nodes.keys()), start)
    best_distance = calc_path_dist(dist_matrix, best_route)

    # print("New cluster")
    noimprove = 0
    while noimprove < 2:
        for swap_first in range(1, N - 2):
            for swap_last in range(swap_first + 1, N - 1):

                dist_diff = calc_distance_difference(dist_matrix, best_route, swap_first, swap_last)

                if dist_diff < 0:
                    best_route = swap(best_route, swap_first, swap_last)
                    best_distance = best_distance + dist_diff
                    # print(best_distance)
                    noimprove = 0

        noimprove += 1

    if best_distance != calc_path_dist(dist_matrix, best_route):
        sys.exit("Negative cost !")
    return best_route, best_distance


def Route_correction(Sequence, start="D0", end="D1"):
    # This function adjust the start and end of the Route.
    # Since we solve a TSP start and end of the Hamiltonion path should be adjusted
    inx_s = np.where(np.array(Sequence) == start)[0][0]
    if inx_s == len(Sequence) - 1:  # when the start of the sequence is at the last position
        if Sequence[0] == end:  # easy the end is at the first just reverse every thing
            Sequence.reverse()
        if Sequence[inx_s - 1] == end:  # 180 degree the opposite of what we need
            Sequence = Sequence[inx_s:] + Sequence[:inx_s]
    else:
        if Sequence[inx_s + 1] == end:
            inx_e = inx_s + 1
            Sequence = Sequence[:inx_e][::-1] + Sequence[inx_e:][::-1]
        if Sequence[inx_s - 1] == end:
            Sequence = Sequence[inx_s:] + Sequence[:inx_s]
    return Sequence


def Two_opt(e_ttime, Nodes, start=None, end=None):
    # This function tackle the special cases and prepare the 2-opt results to be used in both
    # aggregation and dis-aggregation phases.
    # If "start" and "end" are given this means we are in the dis-aggregation phase
    Gnodes = Nodes.route
    N = len(Nodes)
    e_ttime = 1000 * e_ttime
    e_ttime = e_ttime.astype("int")
    BigM = e_ttime.values.max()
    # route that do not need a tsp to be solved
    if end:
        e_ttime[start][end] = e_ttime[end][start] = -1 * BigM

        if N <= 3:
            Gnodes.remove(start)
            Gnodes.remove(end)
            if Gnodes:
                customer = Gnodes[0]
                route = [start, customer, end]
                cost = e_ttime[start][customer] + e_ttime[customer][end]
            else:
                route = [start, end]
                cost = e_ttime[start][end]

            return route, cost/1000
    else:
        if N <= 2:
            return Gnodes, sum(sum(e_ttime.values))/1000

    route, objval = two_opt_Alg(e_ttime, Nodes,)

    if end:
        # we are in dis aggregation that solves TSP to find hamiltonian paths
        route = Route_correction(route, start, end)
        objval += BigM

    return route, objval/1000


def solve(e_ttime, Nodes, start=None, end=None):
    # This function unify the use of tsp solvers
    if 0:
        pass
        # Solve with mathematical model | it needs gurobipy
        # route, objval = TSP_model(e_ttime, Nodes, start, end)
    elif 0:
        pass
        # the concorde wrapper should be downloaded from and installed
        # route, objval = TSP_concorde(e_ttime, Nodes, start, end)
    elif 1:
        pass
        # the LKH3 should be downloaded, make and placed in LKH folder
        # route, objval = LKH3(e_ttime, Nodes, start, end)
    else:
        # Independent implementation of 2-opt
        route, objval = Two_opt(e_ttime, Nodes, start, end)

    return route, objval