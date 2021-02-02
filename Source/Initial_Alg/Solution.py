import copy
from gurobipy import *
from utils import Route_delivery as RD

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
        for route in self.routes:
            route.feasibility_check(Solution.Data)
            violated_time += route.time_violation
            violated_cap += route.cap_violation

        self.time_F = violated_time == 0
        self.time_F = self.time_F and self.total_time < Solution.Data.Total_dis_epsilon
        self.cap_F = violated_cap == 0
        self.feasible = self.time_F and self.cap_F
        self.score = self.obj + alpha * violated_time + beta * violated_cap

    def Find_the_route(self, seq):

        for i, r in enumerate(self.routes):
            if r.is_visit(seq):
                return i

    def Replace(self, route_inx, New_route):
        self.routes[route_inx] = New_route

    def Best_insertion_cost(self, dis, alpha, beta, seq, org_route, des_route):
        # This function calculates the cost of inserting the seq into the des_path.
        # Re calculate the delivery quantities and create a new solution.
        # using the greedy approach to place the seq in the route
        routes = [r for id, r in enumerate(self.routes) if id != des_route and id != org_route]

        if des_route < len(self.routes):
            new_route, flag = Greedy_insertion(dis, Solution.Data.Maxtour, self.routes[des_route], seq)
        else:
            # A new route has to be created
            D0, D1 = Solution.Data.All_seq["D0"][-1], Solution.Data.All_seq["D1"][0]
            new_route = RD.RouteDel([D0, seq, D1])
            flag = 1

        if flag:
            routes.append(new_route)
            # remove the seq from the org route
            updated_org_route = copy.deepcopy(self.routes[org_route])
            seq_inx = self.routes[org_route].route.index(seq)
            updated_org_route.remove(inx=seq_inx)
            if len(updated_org_route) <= 2:
                pass
            else:
                routes.append(updated_org_route)

            # create the new solution object
            new_sol = Solution(routes, alpha, beta)

            return new_sol

        return self


def Greedy_insertion(dis, Maxtour, tour, node):
    # best possible place to insert
    # Worst time complexity O(n**2)
    unable_2_route = []
    best_cost = Maxtour
    best_place = None
    # we go for all positions and penalties the avoid edges.
    for pos in range(len(tour) - 1):
        time_change = tour.insertion_time(dis, pos, node)
        if time_change < best_cost and tour.travel_time + time_change <= Maxtour:
            best_place = pos
            best_cost = time_change
    if best_place != None:
        new_tour = copy.deepcopy(tour)
        new_tour.insert(best_place, node, best_cost)
    else:
        return tour, 0
    # print(f"I could insert with time change {time_change}")
    return new_tour, 1


def Optimal_quantity(Data, routes):
    Gc = Data.Gc
    Quant = Model("Quantity assignment")
    q = Quant.addVars(Gc.nodes, lb=0, name="q")
    tp = Quant.addVars(Gc.nodes, Gc.nodes, lb=0, name="tp")
    tn = Quant.addVars(Gc.nodes, Gc.nodes, lb=0, name="tn")

    Quant.update()

    Quant.setObjective(quicksum(
        Gc.nodes[i]['demand'] - q[i] for i in Gc.nodes)
                     + (Data.Lambda / Data.total_demand) * quicksum(tp[i, j] + tn[i, j] for i, j in tp.keys() ) )

    linear = Quant.addConstrs((tp[i, j] - tn[i, j] +
                             q[i] * Gc.nodes[j]['demand'] - q[j] * Gc.nodes[i]['demand'] == 0
                             for i in Gc.nodes for j in Gc.nodes), name="linear")

    Quant.addConstr(quicksum(q[i] for i in Gc.nodes) <= Data.G.nodes[0]['supply'])
    Quant.addConstrs(quicksum(q[i] for i in route.nodes_in_path) <= Data.Q for route in routes)
    Quant.Params.OutputFlag = 0
    Quant.optimize()

    for route in routes:
        RDP = [0] * Data.NN
        for seq in route[1:-1]:
            for i in seq:
                RDP[i] = q[i].x

        route.RDP[1] = RDP

    return routes, Quant.objVal