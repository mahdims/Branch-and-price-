import random
import numpy as np
import copy
import sys
import networkx as nx
import matplotlib.pyplot as plt
from math import sqrt, exp
from Initial_Alg.Solution import Solution
from Initial_Alg.Builder import greedy_build
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


def bundle_nodes(Data, selected_seq, keeps):

    for inx, seq in enumerate(selected_seq):
        if seq[0] in keeps["N"].keys():
            seq = [seq]
            for a in keeps["N"][seq[0][0]]:
                seq.append(Data.All_seq[a][0])
        selected_seq[inx] = seq

    return selected_seq


def update_f(f, v):
    if isinstance(v, list):
        for node in v:
            f[node[0]] += 1
    else:
        f[v[0]] += 1
    return f


def build_specific_route(Data, alpha, beta):
    routes = [[0, 4, 11, 14], [0, 5, 12, 3, 10, 14], [0, 6, 7, 8, 1, 9, 2, 14]]
    # routes = [[0, 11, 5, 14], [0, 4, 10, 9, 14], [0, 2, 12, 1, 8, 7, 3, 6, 14]]
    D0, D1 = Data.All_seq["D0"][0], Data.All_seq["D1"][0]
    new_routes = []
    for r in routes:
        new_routes.append(RD.RouteDel([D0] + [Data.All_seq[n][0] for n in r[1:-1]] + [D1]))

    new_sol = Solution(new_routes, alpha, beta)
    D = np.array([Data.G.nodes[i]["demand"] for i in range(13)])
    a = np.zeros(13)
    demand = []
    for r in new_sol.routes:
        demand.append(sum(D[i[0]] for i in r[1:-1]))
        a += np.array(r.RDP[1])
    golden_coef = (D - a)/D
    print(demand)
    print(golden_coef)
    return new_sol


def TabuRoute(Data, dis, Pars, keeps, avoids, CurrentSol):
    it = 1
    q = Pars[0] # Number of Nodes to reassign
    P1 = Pars[1] # number of nearest neighbors of node v
    P2 = Pars[2] # Neighborhood size used in GENI
    Teta_min = Pars[3] # Bounds on the number of iterations for which a move is declared tabu
    Teta_max = Pars[4] # Bounds on the number of iterations for which a move is declared tabu
    G = Pars[5]  # A scaling factor used to define an artificial objective function value
    H = Pars[6] # The frequency at which updates alpha and beta
    Max_No_Change = Pars[7] # Maximum number of iterations without any improvement
    alpha = Pars[8]
    beta = Pars[9]

    CurrentSol.score_cal(alpha, beta)
    BestSol = copy.deepcopy(CurrentSol)
    Best_F_Sol = copy.deepcopy(CurrentSol)

    tabu_list = {}
    No_Change_cont = 0

    f = {key[0][0]: 0 for key in Data.All_seq.values()}

    while No_Change_cont <= Max_No_Change and it < 100:
        # print(f"Iteration {it}: current_ob: {CurrentSol.score} | Best solution {Best_F_Sol.score}")
        # Step 1 Node selection
        # Verify the infeasibility of routes
        Route_infeasible = [not r.time_F or not r.cap_F or r.keep_avoid_F for r in CurrentSol.routes]
        # score the sequences based on their appearance in infeasible / feasible routes
        Select_probability = dict([(n, Route_infeasible[inx] + 1 + sum(f.values()) - f[n[0]])
                                   for inx, r in enumerate(CurrentSol.routes) for n in r.route[1:-1]])
        selected_seq = set()
        while len(selected_seq) < q:
            selected_seq.add(utils.roul_wheel(Select_probability))
        selected_seq = list(selected_seq)
        selected_seq = bundle_nodes(Data, selected_seq, keeps)

        # Step 2 (Evaluation of all candidate moves)
        Candidates = {}
        for v in selected_seq:
            f = update_f(f, v)
            Near_nodes = Near_me(Data.NN, v, P1, dis)
            origin_seq = CurrentSol.Find_the_route(v)
            possible_routes_ind = possible_routes(Data, CurrentSol, v, origin_seq, Near_nodes)

            for r_id in possible_routes_ind:
                # test inserting the node to a possible path

                P_Sol = CurrentSol.Best_insertion(dis, alpha, beta, v, origin_seq, r_id)
                # Check if the move is Tabu
                if (v[0], r_id) in tabu_list.keys():

                    if (1-P_Sol.feasible)*(P_Sol.score < BestSol.score) or P_Sol.feasible*(P_Sol.score < Best_F_Sol.score):
                        Candidates[(v[0], r_id)] = P_Sol
                else:
                    name = (v[0], r_id)
                    Candidates[name] = P_Sol

        # Step 3 Identification of best move
        if len(Candidates) != 0:

            inx, Best_New_Sol = min(Candidates.items(), key=lambda x:x[1].score)

            # Step 4 Next current solution
            if Best_New_Sol.score < CurrentSol.score: # or accept(Best_New_Sol, BestSol, temp):
                CurrentSol = copy.deepcopy(Best_New_Sol) # change the next best sol
                No_Change_cont = 0
            else:
                No_Change_cont += 1

            if CurrentSol.feasible and CurrentSol.score <= Best_F_Sol.score:
                Best_F_Sol = CurrentSol
                # update the best feasible solution
            if CurrentSol.score <= BestSol.score:
                BestSol = CurrentSol

            # Add move to the tabu list
            tabu_list[inx] = random.randint(Teta_min, Teta_max)
        else:
            print("Empty candidate !!")
        # Update the tabu list
        tabu_moves = list(tabu_list.keys())
        for i in tabu_moves:
            tabu_list[i] -= 1
            if tabu_list[i] == 0:
                del tabu_list[i]
        it += 1
        if No_Change_cont >= 8:
            print("------- Restart ------")
            CurrentSol = greedy_build(Data, dis, alpha, beta,flag="random")
            No_Change_cont = 0

    print('Iteration %d : Best F solution Obj = %s' % (it, Best_F_Sol.obj))
    return Best_F_Sol


def build_a_random_sol(Data, dis, alpha, beta):
    starting_angel = random.randint(0, 360)
    print(f"I started the initial sol once again with Angle {starting_angel}")
    All_seq = change_angle_from_depot(Data.All_seq, starting_angel)
    routes = Sweep(Data, dis, All_seq)
    new_sol = Solution(routes, alpha, beta)
    return new_sol


def Initial_feasibleSol(Data, dis, keeps, avoids):
    Data.Penalty = max(dis.values()) * 10
    RD.RouteDel.nodes2keep = keeps["E"]
    RD.RouteDel.nodes2avoid = avoids["E"]
    RD.RouteDel.Data = Data
    RD.dis = dis

    Solution.Data = Data
    Solution.nodes2avoid = avoids["E"]
    Solution.nodes2keep = keeps["E"]
    Seq.Sequence.dis = dis

    alpha = 100
    beta = 100

    N_of_Node2Change = int(Data.NN / 5)
    N_of_near_node = int(Data.NN / 3)
    pars = (N_of_Node2Change, N_of_near_node, None, 2, 5, 0.1, 2, 1000, alpha, beta)

    initial_Sol_count = 0
    no_success = 0
    new_sols = []
    while initial_Sol_count < 1 and no_success < 50:

        new_sol = greedy_build(Data, dis,  alpha, beta)
        # new_sol = build_a_random_sol(Data, dis, alpha, beta)
        # new_sol = build_specific_route(Data, alpha, beta)
        print(f"The initial solution {new_sol.score}")
        new_sol = TabuRoute(Data, dis, pars, keeps, avoids, new_sol)
        # sys.exit(new_sol.routes)
        if new_sol.feasible:
            initial_Sol_count += 1
            new_sols.append(new_sol)
        else:
            print("Keep list")
            print(keeps)
            print("Avoids list")
            print(avoids)
            input("Press any key to continue")
            no_success += 1

    return new_sols, no_success < 50
