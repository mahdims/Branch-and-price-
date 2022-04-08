import copy
import sys
from gurobipy import *
from utils import Route_delivery as RD
from utils import utils
from utils import Opt_delivery as OptD
# Class for solution of the initial heuristic (TabuRoute)


class Solution:
    Data = None

    def __init__(self, routes, alpha, beta):
        self.routes = routes
        self.obj = 0
        self.total_time = sum([r.travel_time for r in routes])
        self.score = 0
        self.time_F = 0
        self.cap_F = 0
        self.feasible = 0
        self.feasible0 = 0
        # Calculate the delivery quantity of all seq (by mathematical model) add to the RDP[1]
        self.routes, self.q_obj = Optimal_quantity(Solution.Data, routes)
        # Calculate the master objective value by for a total solution
        self.obj_calc(self.q_obj)
        # As a reminder, alpha and beta are the penalty cost for being infeasible regarding the mac tour and vehicle cap
        self.score_cal(alpha, beta)

    def obj_calc(self, q_obj):
        self.obj = q_obj + (Solution.Data.Gamma / Solution.Data.R) * \
                   max(0, Solution.Data.Total_dis_epsilon - self.total_time)

    def score_cal(self, alpha, beta):
        violated_time = 0
        violated_cap = 0
        keep_avoid = 0
        for route in self.routes:
            route.feasibility_check(Solution.Data)
            violated_time += route.time_violation
            violated_cap += route.cap_violation
            keep_avoid += (1-route.keep_avoid_F)
        self.time_F = violated_time == 0
        self.cap_F = violated_cap == 0
        self.keep_avoid_F = keep_avoid == 0
        self.feasible0 = self.time_F and self.cap_F
        self.feasible = self.time_F and self.cap_F and self.keep_avoid_F
        self.score = self.obj + alpha * violated_time + beta * violated_cap + Solution.Data.Penalty * keep_avoid

    def Find_the_route(self, seqs):
        inx = set()
        origin_seq = {}
        if isinstance(seqs, list):
            pass
        else:
            seqs = [seqs]

        for seq in seqs:
            for i, r in enumerate(self.routes):
                if r.is_visit(seq) != -1:
                    origin_seq[seq] = i
                    inx.add(i)
        return origin_seq # list(inx)

    def Replace(self, route_inx, New_route):
        self.routes[route_inx] = New_route

    def Best_insertion(self, dis, alpha, beta, seqs, seqs_origin, des_route):
        # This function calculates the cost of inserting the seq into the des_path.
        # Re calculate the delivery quantities and create a new solution.
        # using the greedy approach to place the seq in the route]
        flag = 1
        All_seq_org = list(set(seqs_origin.values()))
        routes = {id:r for id, r in enumerate(self.routes) if id != des_route and id not in All_seq_org}

        for org in All_seq_org:
            routes[org] = copy.deepcopy(self.routes[org])

        if not isinstance(seqs, list):
            seqs = [seqs]
        else:
            # we have some keeps members here
            pass

        if des_route < len(self.routes):
            new_route = copy.deepcopy(self.routes[des_route])
            for seq in seqs:

                if new_route.is_visit(seq) == -1:
                    new_route, flag = Greedy_insertion(dis, Solution.Data.Maxtour, new_route, seq)

                    if flag:
                        routes[seqs_origin[seq]] = remove_seq_from_route(routes[seqs_origin[seq]], seq)
                    else:
                        break
        else:
            # A new route has to be created
            D0, D1 = Solution.Data.All_seq["D0"][-1], Solution.Data.All_seq["D1"][0]
            temp_list = [D0]
            for seq in seqs:
                temp_list.append(seq)
                routes[seqs_origin[seq]] = remove_seq_from_route(routes[seqs_origin[seq]], seq)
            try:
                new_route = RD.RouteDel(temp_list + [D1], "Init_new_route")
            except KeyError:
                sys.exit(f"Line 100 Solution : \n {seqs}")
            flag = 1

        if flag:
            routes[des_route] = new_route

            clean_route = []
            for r in routes.values():
                if len(r) <= 2:
                    pass
                else:
                    clean_route.append(r)

            # The new delivery quantities are calculated in Solution __init__
            # The penalty for keep and avoid violation is added to the solution score
            new_sol = Solution(clean_route, alpha, beta)

            return new_sol

        return self


def remove_seq_from_route(route, seq):

    inx = route.where(seq)
    route.remove(inx=inx)

    return route


def Greedy_insertion(dis, Maxtour, tour, node):
    # best possible place to insert
    # Worst time complexity O(n**2)
    unable_2_route = []
    best_cost = float("inf")
    Best_time_change = 0
    best_place = None
    # we go for all positions and penalties the avoid edges.
    for pos in range(len(tour) - 1):
        fitness_change, time_change = tour.insertion_time(dis, pos, node)
        if fitness_change < best_cost and tour.travel_time + time_change <= Maxtour:
            best_place = pos
            best_cost = fitness_change
            Best_time_change = time_change

    if best_cost != float("inf"):
        new_tour = copy.deepcopy(tour)
        new_tour.insert(best_place, node, Best_time_change)
    else:
        return tour, 0
    # print(f"I could insert with time change {time_change}")
    return new_tour, 1


def Optimal_quantity(Data, routes):
    Gc = Data.Gc
    Q = Data.Q
    C = Data.G.nodes[0]["supply"]
    C_remain = C
    r_demand = [sum([Gc.nodes[i]['demand'] for i in r.nodes_in_path]) for r in routes]
    un_decided = [i for i in range(len(routes))]
    while len(un_decided) != 0:
        vio_route = []
        Beta = C_remain / max(C_remain, sum([r_demand[r_inx] for r_inx in un_decided]))
        for r_inx in un_decided:
            if Beta * r_demand[r_inx] > Q:
                vio_route.append(r_inx)

        if len(vio_route) == 0:
            for r_inx in un_decided:
                RDP = [0] * Data.NN
                for i in routes[r_inx].nodes_in_path:
                    RDP[i] = round(Gc.nodes[i]['demand'] * Beta, 10)
                routes[r_inx].set_RDP(RDP)
            break
        else:
            for r_inx in vio_route:
                beta_K = Q / r_demand[r_inx]
                RDP = [0] * Data.NN
                for i in routes[r_inx].nodes_in_path:
                    RDP[i] = round(Gc.nodes[i]['demand'] * beta_K, 10)
                routes[r_inx].set_RDP(RDP)
                un_decided.remove(r_inx)
                C_remain -= Q

        # print(f"Ideal demand: {Data.total_demand/Data.M}")

    RDPS = {i: routes[i].RDP[1] for i in range(len(routes))}
    obj = utils.calculate_the_obj(Data, routes, RDPS)

    D_rate = {}
    D_correct = {}
    D_sum = []
    for i, r in RDPS.items():
        D_rate[i] = [n/Data.G.nodes[j]["demand"] for j, n in enumerate(r) if j != 0]
        D_correct[i] = all([n <= Data.G.nodes[j]["demand"] for j, n in enumerate(r) if j != 0])
        D_sum.append(sum(r))
        if D_sum[i] < C/Data.total_demand * r_demand[i] and round(D_sum[i],0) != Q:
            print("The assigned deliveries in the initial algorithm has some problem")
        if not D_correct[i]:
            print("There is a problem , more than demand delivery")

    return routes, obj