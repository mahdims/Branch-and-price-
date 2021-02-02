import random
import numpy as np
import copy
import sys
import networkx as nx
import matplotlib.pyplot as plt
from math import sqrt
from Initial_Alg.Solution import Solution
from Initial_Alg import TSP_Solver
from utils import Route_delivery as RD
from utils import Seq, utils


##### Functions 
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
    vehicleCap = Data.Q
    temp_Customers = {key: val for key, val in All_seq.items() if key != "D0" and key != "D1"}
    temp_Customers = sorted(temp_Customers.values(), key=lambda x: x[0].AngleWithDepot, reverse=False)
    clusters = list()

    cap = 0
    depot_list = copy.deepcopy( All_seq["D0"])
    depot_list, depot = Seq.select_starting_edge(depot_list)
    tempCluster = [depot]

    while len(temp_Customers):
        cur_seq = temp_Customers.pop(0)
        if cap + cur_seq[0].delivery <= vehicleCap or len(clusters) == Data.M-1: # and tour_lenght + Distance( tempCluster[-1] , currCust[0] ) <= Mxtourlenght :
            tempCluster.append(cur_seq[0])
            cap += cur_seq[0].delivery
            # tour_lenght += Distance( tempCluster[-2] , currCust[0] ) # based on shoretst path
        else:
            # close the previous route
            clusters.append(tempCluster + All_seq["D1"])
            # create a new cluster
            depot_list, depot = Seq.select_starting_edge(depot_list)
            tempCluster = [depot]
            cap = 0
            tempCluster.append(cur_seq[0])
            cap += cur_seq[0].delivery
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
        dis_from_N = [Distance(i, n, length) for i in range(1, NN)]
        Sorted_inx = np.argpartition(dis_from_N, int(P1))+1
        inx[n] = Sorted_inx[:P1]
    
    return inx


def possible_routes(Data, CurrentSol, V, V_route_inx, Near_nodes):
    # This function find the index of routes that nodes/node in v can be inserted into
    Possible_rou_index = []
    for i, C_route in enumerate(CurrentSol.routes):
        for v in V:
            if V_route_inx != i and any([k in C_route.nodes_in_path for k in Near_nodes[v]]):
                Possible_rou_index.append(i)
    if len(CurrentSol.routes) < Data.M:
        Possible_rou_index.append(len(CurrentSol.routes))

    if len(Possible_rou_index) == 0:
        # All near node in the same route and reached M
        routes_inxs = list(range(len(CurrentSol.routes)))
        routes_inxs.remove(V_route_inx)
        Possible_rou_index.append(np.random.choice(routes_inxs))
    return list(set(Possible_rou_index))

    
def TabuRoute(Data, dis, Pars, CurrentSol):
    it = 1
    q = Pars[0] # Number of Nodes to reassign
    P1 = Pars[1] # number of nearest neighbors of node v
    P2 = Pars[2] # Neighborhood size used in GENI
    Teta_min = Pars[3] # Bounds on the number of iterations for which a move is declared tabu
    Teta_max = Pars[4] # Bounds on the number of iterations for which a move is declared tabu
    G = Pars[5]  # A scaling factor used to define an artificial objective function value
    H = Pars[6] # The frequency at which updates alpha and beta
    Max_No_Change = Pars[7] # Maximum number of iterations without any improvement
    alpha = Pars[7]
    beta = Pars[8]

    CurrentSol.score_cal(alpha, beta)
    Last_Current = copy.deepcopy(CurrentSol) 
    BestSol = copy.deepcopy(CurrentSol)   
    Last_Best = copy.deepcopy(CurrentSol) 
    Best_F_Sol = copy.deepcopy(CurrentSol)  
    Last_F_Best = copy.deepcopy(CurrentSol)
    
    delta = 200
    delta_list = []
    f = np.zeros(Data.NN)
    tabu_list = {}
    USconter = 0
    No_Change_cont = 0
    iter_count = 0
    while No_Change_cont <= Max_No_Change:
        # print(f"Iteration {iter_count}: current_ob: {Best_F_Sol.score}")
        iter_count += 1
        # Step 1 Node selection
        # Verify the infeasibility of routes
        Route_infeasible = [not r.time_F or not r.cap_F for r in CurrentSol.routes]
        # score the sequences based on their appearance in infeasible / feasible routes
        Select_probability = dict([(n, Route_infeasible[inx]+1)
                                   for inx, r in enumerate(CurrentSol.routes) for n in r.route[1:-1]])
        selected_seq = set()
        while len(selected_seq) < q:
            selected_seq.add(utils.roul_wheel(Select_probability))
        selected_seq = list(selected_seq)

        # Step 2 (Evaluation of all candidate moves)
        Candidates = {}
        for v in selected_seq:
            Near_nodes = Near_me(Data.NN, v, P1, dis)
            V_route_inx = CurrentSol.Find_the_route(v)
            possible_routes_ind = possible_routes(Data, CurrentSol, v, V_route_inx, Near_nodes)
            
            for r_id in possible_routes_ind:
                # test inserting the node to a possible path

                P_Sol = CurrentSol.Best_insertion_cost(dis, alpha, beta, v, V_route_inx, r_id)

                # Check if the move is Tabu
                if (v[0], r_id) in tabu_list.keys():

                    if (1-P_Sol.feasible)*(P_Sol.score < BestSol.score) or P_Sol.feasible*(P_Sol.score < Best_F_Sol.score):
                        Candidates[(v[0], V_route_inx, r_id)] = P_Sol
                else:
                    if P_Sol.score < BestSol.score:
                        name = (v[0], V_route_inx, r_id)
                        Candidates[name] = P_Sol
                    else:
                        P_Sol.score = P_Sol.score + delta * sqrt(Data.M) * G * f[v[0]]
                        name = (v[0], V_route_inx, r_id)
                        Candidates[name] = P_Sol

        # Step 3 Identification of best move
        if len(Candidates) != 0:
            Best_New_Sol = min(Candidates.items(), key=lambda x: x[1].score)

            # Step 4 Next current solution
            if Best_New_Sol[1].score > CurrentSol.score and CurrentSol.feasible and USconter == 0:
                # Run the US on Bestsol
                US = 0
                USconter = 1
            else:
                USconter = 0
                Last_Current = CurrentSol # keep the last sol
                CurrentSol = Best_New_Sol[1] # change the next best sol
                
                # Step 5 Update
                Last_F_Best = Best_F_Sol
                Last_Best = BestSol 
                
                if CurrentSol.feasible and CurrentSol.score <= Best_F_Sol.score:
                    Best_F_Sol = CurrentSol # update the best fesibel solution    
                if CurrentSol.score <= BestSol.score:
                    BestSol = CurrentSol
                    
                f[Best_New_Sol[0][0]] += 1 # update the number of times 5that node v reallocates
                # Add move to the tabu list
                tabu_list[Best_New_Sol[0][0], Best_New_Sol[0][1]] = it+random.randint(Teta_min, Teta_max)

        # Update the delta
        delta_list.append(abs(CurrentSol.score-Last_Current.score))
        delta = max(delta_list)
        # calculate the no change counter
        if Last_Best.score == BestSol.score and Last_F_Best.score == Best_F_Sol.score:
            No_Change_cont += 1
        else:
            No_Change_cont = 0
        # Update the tabu list
        tabu_moves = list(tabu_list.keys())
        for i in tabu_moves:
            tabu_list[i] -= 1
            if tabu_list[i] == 0:
                del tabu_list[i]
        # print('Iteration %d : Best solution Obj = %s' %(it,Best_F_Sol.score))
        it += 1
    print('Iteration %d : Best F solution Obj = %s' % (it, Best_F_Sol.obj))
    return Best_F_Sol


def Initial_feasibleSol(Data, dis, edges2keep, edges2avoid):
    RD.RouteDel.edges2keep = edges2keep["N"]
    RD.RouteDel.edges2avoid = edges2avoid["N"]
    RD.RouteDel.Data = Data
    RD.dis = dis

    Solution.Data = Data
    Solution.edges2avoid = edges2avoid["N"]
    Solution.edges2keep = edges2keep["N"]
    Seq.Sequence.dis = dis

    alpha = 1000
    beta = 1000

    initial_Sol_count = 0
    no_success =0
    new_sols = []
    while initial_Sol_count < 1 and no_success < 50:
        starting_angel = random.randint(0, 360)
        # print(f"I started the initial sol once again with Angle {starting_angel}")
        All_seq = change_angle_from_depot(Data.All_seq, starting_angel)
        routes = Sweep(Data, dis, All_seq)
        new_sol = Solution(routes, alpha, beta)

        N_of_Node2Change = int(Data.NN/5)
        N_of_near_node = int(Data.NN/3)
        pars = (N_of_Node2Change, N_of_near_node, None, 3, 6, 0.1, 3, 7, alpha, beta)

        new_sol = TabuRoute(Data, dis, pars, new_sol)

        if new_sol.feasible:
            initial_Sol_count += 1
            new_sols.append(new_sol)
        else:
            no_success += 1

    return new_sols, initial_Sol_count >=1
