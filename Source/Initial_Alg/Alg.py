"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""

import random
import numpy as np
import copy
import sys
from loguru import logger
import networkx as nx
import matplotlib.pyplot as plt
from math import sqrt, exp
from Initial_Alg.Solution import Solution
from Initial_Alg.Builder import greedy_build, CW
from Initial_Alg import TSP_Solver
from utils import Route_delivery as RD
from utils import Seq, utils


def Distance(i, j, length):
    if i == j:
        return 1000000000000000000
    return length[i, j]


def get_route(NN, nodes, index):
    route = []
    for ind in index[0:-1]:
        route.append(nodes[ind])
    route.append(NN+1)
    return route


def change_angle_from_depot(All_seq, starting_angel):
    for seq_list in All_seq.values():
        for seq in seq_list:
            seq.AngleWithDepot = (seq.AngleWithDepot+starting_angel) % 360
    return All_seq


def Sweep(Data, dis, All_seq):
    Ideal_demand = Data.total_demand/Data.M
    temp_Customers = {key: val for key, val in All_seq.items() if key != "D0" and key != "D1"}
    temp_Customers = sorted(temp_Customers.values(), key=lambda x: x[0].AngleWithDepot, reverse=False)
    clusters = list()

    route_demand = 0
    depot_list = copy.deepcopy(All_seq["D0"])
    depot_list, depot = Seq.select_starting_edge(depot_list)
    tempCluster = [depot]

    while len(temp_Customers):
        cur_seq = temp_Customers.pop(0)
        if route_demand + cur_seq[0].demand <= Ideal_demand or len(clusters) == Data.M-1: # and tour_lenght + Distance( tempCluster[-1] , currCust[0] ) <= Mxtourlenght :
            tempCluster.append(cur_seq[0])
            route_demand += cur_seq[0].demand
            # tour_lenght += Distance( tempCluster[-2] , currCust[0] ) # based on shoretst path
        else:
            # close the previous route
            clusters.append(tempCluster + All_seq["D1"])
            # create a new cluster
            depot_list, depot = Seq.select_starting_edge(depot_list)
            tempCluster = [depot]
            route_demand = 0
            tempCluster.append(cur_seq[0])
            route_demand += cur_seq[0].demand
            # tour_length += Distance( tempCluster[-2] , currCust[0] )

    clusters.append(tempCluster+All_seq["D1"])
    routes = []
    for p in clusters:
        new_RD = RD.RouteDel(p)
        new_RD.calc_time(dis)
        routes.append(new_RD)

    return routes


def draw_the_solution(Data, paths):
    # obsolete
    NN = Data.NN
    testgraph = nx.Graph()
    testgraph.add_nodes_from(range(NN) + [NN+1])
    for r in paths:
        print(r.route)
        print("Route cost:", r.travel_time)
        testgraph.add_path(r.route)
    nx.draw(testgraph)
    plt.show()


def node2remove(path):
    newtarveltime = {}
    for k, n in enumerate(path.route[1:-1]):
        i = k+1
        newtarveltime[n] = \
            path.travel_time-Distance(path.route[i-1],n)-Distance(n,path.route[i+1])+Distance(path.route[i-1],path.route[i+1])
        if newtarveltime[n] <= Data.Maxtour:
            return n
    best_node = min(newtarveltime, key=newtarveltime.get)
    return best_node


def Near_me(NN, Ns, P1, length):
    # finds P1 nodes near to each node in NS (a sequence)
    inx = {}
    for n in Ns:
        if isinstance(n, Seq.Sequence):
            n = n[0]
        dis_from_N = [Distance(i, n, length) for i in range(1, NN)]
        Sorted_inx = np.argpartition(dis_from_N, int(P1))+1
        inx[n] = Sorted_inx[:P1]
    
    return inx


def possible_routes(Data, CurrentSol, V, seqs_origin, Near_nodes):
    # This function find the index of routes that nodes/node in v can be inserted into
    Possible_rou_index = []
    All_nears = set([i for a in Near_nodes.values() for i in a])
    routes_with_near = [i for i, C_route in enumerate(CurrentSol.routes) for k in All_nears if C_route.is_visit(k)]
    routes_with_near = set(routes_with_near)
    All_seq_org = list(set(seqs_origin.values()))

    for i in routes_with_near:
        if len(All_seq_org) <= 1:
            if i not in All_seq_org:
                Possible_rou_index.append(i)
        else:
            Possible_rou_index.append(i)

    if len(CurrentSol.routes) < Data.M:
        Possible_rou_index.append(len(CurrentSol.routes))

    if len(Possible_rou_index) == 0:
        # Go wild and add all as the possible route
        for i in range(len(CurrentSol.routes)):
            if len(All_seq_org) <= 1:
                if i not in All_seq_org:
                    Possible_rou_index.append(i)
            else:
                Possible_rou_index.append(i)

    return Possible_rou_index


def accept(sol, best, temp):
    if sol.score < best.score:
        return 1
    print(f"Acceptance rate : {exp(-1 * (sol.score - best.score) / temp)}")
    if random.random() <= exp(-1 * (sol.score - best.score) / temp):
        return 1
    else:
        return 0


def is_branched(node, avoids):
    for i, j in avoids:
        if node[0] == i or node[0] == j:
            return 1
    return 0


def bundle_nodes(Data, All_seq, selected_seq, keeps):
    # We move the connected keep edges around togther // We are not using this anymore
    for inx, seq in enumerate(selected_seq):
        first_member = seq[0]
        if first_member in keeps["N"].keys():
            second_member = seq[1]
            seq = [seq]
            for a in keeps["N"][first_member]:
                if a == second_member: continue
                seq_inx = (min(a, first_member), max(a, first_member))
                try:
                    seq.append(All_seq[seq_inx][0])
                except KeyError:
                    print(All_seq)
                    print(selected_seq)
                    sys.exit(f"Key error {seq_inx} line 173 in Alg.py")
        selected_seq[inx] = seq

    return selected_seq


def update_f(f, v):
    if isinstance(v, list):
        for node in v:
            f[node[0]] += 1
    else:
        f[v[0]] += 1
    return f


def build_specific_route(Data, All_seq, alpha, beta):
    # routes = [[0, 4, 11, 14], [0, 5, 12, 3, 10, 14], [0, 6, 7, 8, 1, 9, 2, 14]]
    # routes = [[0, 11, 5, 14], [0, 4, 10, 9, 14], [0, 2, 12, 1, 8, 7, 3, 6, 14]]
    routes = [[0, 2, 12, 1, 9, 11, 14], [0, 3, 8, 4, 14], [0, 6, 7, 5, 10, 14]]
    D0, D1 = All_seq["D0"][0], All_seq["D1"][0]
    new_routes = []
    for r in routes:
        new_routes.append(RD.RouteDel([D0] + [All_seq[n][0] for n in r[1:-1]] + [D1], "init_specific"))

    new_sol = Solution(new_routes, alpha, beta)

    return new_sol


def TabuRoute(Data, All_seq, dis, Pars, keeps, avoids, CurrentSol):
    it = 1
    q = Pars[0] # Number of Nodes to reassign
    P1 = Pars[1] # number of nearest neighbors of node v
    P2 = Pars[2] # Neighborhood size used in GENI
    Teta_min = Pars[3] # Bounds on the number of iterations for which a move is declared tabu
    Teta_max = Pars[4] # Bounds on the number of iterations for which a move is declared tabu
    G = Pars[5]  # A scaling factor used to define an artificial objective function value
    H = Pars[6] # The frequency at which updates alpha and beta
    Max_No_Change = Pars[7] # Maximum number of iterations without any improvement

    CurrentSol.score_cal()
    BestSol = CurrentSol.make_a_copy()
    Best_F_Sol = CurrentSol.make_a_copy()
    Best_F0_sol = CurrentSol.make_a_copy()

    tabu_list = {}
    No_Change_cont = 0

    f = {key[0][0]: 0 for key in All_seq.values()}

    while No_Change_cont <= Max_No_Change and it < 100:
        # print(f"Iteration {it}: current_ob: {CurrentSol.score} | Best solution {Best_F_Sol.score}")
        # Step 1 Node selection
        # Verify the infeasibility of routes
        Route_infeasible = [not r.time_F or not r.cap_F or not r.keep_avoid_F for r in CurrentSol.routes]
        # score the sequences based on their appearance in infeasible / feasible routes
        Select_probability = dict([(n, 3 * Route_infeasible[inx] + 1 + sum(f.values()) - f[n[0]])
                                   for inx, r in enumerate(CurrentSol.routes) for n in r.route[1:-1]])
        selected_seq = set()
        while len(selected_seq) < q:
            selected_seq.add(utils.roul_wheel(Select_probability))
        selected_seq = list(selected_seq)
        # selected_seq = bundle_nodes(Data, All_seq, selected_seq, keeps)

        # Step 2 (Evaluation of all candidate moves)
        Candidates = {}
        for v in selected_seq:
            f = update_f(f, v)
            Near_nodes = Near_me(Data.NN, v, P1, dis)
            origin_seq = CurrentSol.Find_the_route(v)
            possible_routes_ind = possible_routes(Data, CurrentSol, v, origin_seq, Near_nodes)

            for r_id in possible_routes_ind:
                # test inserting the node to a possible path
                P_Sol = CurrentSol.Best_insertion(dis, v, origin_seq, r_id)
                if isinstance(P_Sol, int):
                    continue

                # before you do anything else pick  this solution
                # feasible without considering avoiding and keeping edges
                if P_Sol.feasible0 and P_Sol.obj < Best_F0_sol.obj:
                    Best_F0_sol = P_Sol.make_a_copy()

                # Check if the move is Tabu
                if (v[0], r_id) in tabu_list.keys():
                    if (1-P_Sol.feasible)*(P_Sol.score < BestSol.score) or \
                            P_Sol.feasible*(P_Sol.score < Best_F_Sol.score):
                        Candidates[(v[0], r_id)] = P_Sol.make_a_copy()
                else:
                    name = (v[0], r_id)
                    Candidates[name] = P_Sol.make_a_copy()

        # Step 3 Identification of best move
        if len(Candidates) != 0:

            inx, Best_New_Sol = min(Candidates.items(), key=lambda x:x[1].score)
            # Step 4 Next current solution
            if Best_New_Sol.score < CurrentSol.score: # or accept(Best_New_Sol, BestSol, temp):
                CurrentSol = Best_New_Sol.make_a_copy() # change the next best sol
                No_Change_cont = 0
            else:
                No_Change_cont += 1

            if CurrentSol.feasible and CurrentSol.score <= Best_F_Sol.score:
                Best_F_Sol = CurrentSol.make_a_copy()
                # update the best feasible solution
            if CurrentSol.score <= BestSol.score:
                BestSol = CurrentSol.make_a_copy()

            # Add move to the tabu list
            tabu_list[inx] = random.randint(Teta_min, Teta_max)
        else:
            No_Change_cont += 1
        # Update the tabu list
        tabu_moves = list(tabu_list.keys())
        for i in tabu_moves:
            tabu_list[i] -= 1
            if tabu_list[i] == 0:
                del tabu_list[i]
        it += 1
        if No_Change_cont >= 8:
            # print("------- Restart ------")
            CurrentSol = greedy_build(Data, All_seq, dis, flag="random")
            No_Change_cont = 0

    # print('Iteration %d : Best F solution Obj = %s Total time = %s ' % (it, Best_F_Sol.obj, Best_F_Sol.total_time))
    if not Best_F0_sol.feasible:
        Best_F0_sol = 0
        # print(f"I found even better feasible solution with obj = {Best_F0_sol.obj}")
        pass

    # TEST:
    comul = 0
    for i in range(len(Best_F_Sol.routes)):
        comul += sum(Best_F_Sol.routes[i].RDP[1])
    if round(comul, 0) > Solution.Data.G.nodes[0]["supply"]:
        print(f"With total delivery {comul}")

    return Best_F_Sol, Best_F0_sol


def build_a_random_sol(Data,All_seq, dis, alpha, beta):
    starting_angel = random.randint(0, 360)
    print(f"I started the initial sol once again with Angle {starting_angel}")
    All_seq = change_angle_from_depot(All_seq, starting_angel)
    routes = Sweep(Data, dis, All_seq)
    new_sol = Solution(routes, alpha, beta)
    return new_sol


def Initial_feasibleSol(Data, All_seq,  dis, keeps, avoids, number_of_sols):
    Data.Penalty = max(dis.values()) * 10
    RD.RouteDel.nodes2keep = keeps["E"]
    RD.RouteDel.nodes2avoid = avoids["E"]
    RD.RouteDel.Data = Data
    RD.dis = dis

    Solution.Data = Data
    Solution.nodes2avoid = avoids["E"]
    Solution.nodes2keep = keeps["E"]
    Seq.Sequence.dis = dis

    Solution.alpha = 100
    Solution.beta = 100

    N_of_Node2Change = int(Data.NN / 5)
    N_of_near_node = int(Data.NN / 3)
    pars = (N_of_Node2Change, N_of_near_node, None, 2, 5, 0.1, 2, 1000)

    initial_Sol_count = 0
    no_success = 0
    new_sols = []
    best_F0_sol = 0
    while initial_Sol_count < number_of_sols and no_success < 2:

        new_sol = CW(Data, All_seq, dis)
        #new_sol = greedy_build(Data, All_seq,dis,  alpha, beta)
        # new_sol = build_a_random_sol(Data, dis, alpha, beta)
        #if len(keeps["E"]) == 0 and len(avoids["E"]) ==0: # Only run for the root node
        #    new_sol = build_specific_route(Data, All_seq, alpha, beta)
        logger.info(f"The initial solution generated by CW for Tabu search is {round(new_sol.score,2)}")
        new_sol, good_sol = TabuRoute(Data, All_seq, dis, pars, keeps, avoids, new_sol)

        # sys.exit(new_sol.routes)
        if new_sol.feasible:
            initial_Sol_count += 1
            new_sols.append(new_sol.make_a_copy())
            logger.info(f"The TS optimal solution {round(new_sol.score,2)}")

        else:
            no_success += 1
            logger.warning(f"TS failed {no_success} times to find a feasible solution")
            if len(new_sols) >=1:
                break
            # input("Press any key to continue")

        if good_sol != 0:
            #print(f"UB with TS with out edge branching {good_sol.score}")
            if best_F0_sol == 0:
                best_F0_sol = good_sol.make_a_copy()
            elif good_sol.obj < best_F0_sol.obj:
                best_F0_sol = good_sol.make_a_copy()

    return new_sols, best_F0_sol, len(new_sols) != 0
