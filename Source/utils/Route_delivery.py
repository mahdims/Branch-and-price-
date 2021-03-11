import numpy as np
import networkx as nx
import sys
from utils import utils,Seq
# This is the route deliveries class that is used in initial solution class and Column generation _ branch and price


class RouteDel:
    E2K = None
    nodes2keep = None
    nodes2avoid = None
    routes_set = []
    Data = []
    dis = []

    def __init__(self, route):
        self.route = route
        # I trust that sequence of nodes in path is correct (calculated by build_nodes)
        self.nodes_in_path = []
        self.build_nodes()
        # calculate the travel time inplace
        self.travel_time = 0
        self.calc_time(dis)
        # We don't update the deliveris yet
        self.RDP = {}
        self.total_deliveries = 0
        # the four below attr calculated in feasibility_check
        self.cap_violation = None
        self.time_violation = None
        self.cap_F = None
        self.time_F = None
        self.keep_avoid_F = 0
        self.feasibility_check(RouteDel.Data)

    def __len__(self):
        return len(self.route)

    def __repr__(self):
        return f"{self.route}"

    def __getitem__(self, inx):
        try:
            return self.route[inx]
        except KeyError:
            sys.exit(f"Index {inx} is not in list with {len(self.route)}")

    def build_nodes(self):
        self.nodes_in_path = []
        if len(self.route[0]) > 1:
            self.nodes_in_path += self.route[0][1:]
        for n in self.route[1:-1]:
            self.nodes_in_path += n.string

    def calc_time(self, dis):
        self.travel_time = self.route[0].string_time
        PreNode = self[0]
        for n_inx, n in enumerate(self.route[1:-1]):
            self.travel_time += dis[PreNode[-1], n[0]] + n.string_time
            PreNode = n
        # self.travel_time += RouteDel.Data.Penalty * (1 - utils.avoid_check(self, RouteDel.nodes2avoid))
        # self.travel_time += RouteDel.Data.Penalty * (1 - utils.keep_check(self, RouteDel.nodes2keep))

    def feasibility_check(self, Data):
        self.time_violation = max(0, self.travel_time - Data.Maxtour)
        self.time_F = self.time_violation == 0
        self.cap_violation = max(0, round(self.total_deliveries, 0) - Data.Q)
        self.cap_F = self.cap_violation == 0
        self.keep_avoid_F = 2 - utils.avoid_check(self, RouteDel.nodes2avoid) - utils.keep_check(self, RouteDel.nodes2keep)

    def where(self, node):
        if isinstance(node, Seq.Sequence):
            node = node[0]
        for inx, seq in enumerate(self.route):
            if node in seq:
                return inx

    def is_visit(self, sq):
        try:
            if isinstance(sq, Seq.Sequence):
                for r_seq in self.route:
                    if sq.string == r_seq.string:
                        return 1
            else:
                if sq in self.nodes_in_path:
                    return 1
                elif sq == 0:
                    return 1
        except :
            print("Stop at is visit !! ")
            sys.exit(self.route)

        return 0

    def insertion_time(self, dis, i, p):
        # the total route time change with inserting seq p in location i (add penalty Data.Maxtour if avoid edges)
        try:
            time = dis[self.route[i][-1], p[0]] + dis[p[-1], self.route[i + 1][0]] \
                   + p.string_time - dis[self.route[i][-1], self.route[i + 1][0]]
        except:
            sys.exit((self.route[i], self.route[i + 1], p))

        '''
        feasibility = 0 
        # Adding the penalty cost for avoid and violation of keeps
        if utils.avoid_NR_check(self, p, RouteDel.nodes2avoid):
            feasibility += 1
            # time += RouteDel.Data.Penalty
        if utils.keep_NR_check(self, p, RouteDel.nodes2keep):
            feasibility += 1
            # time += RouteDel.Data.Penalty

        # deduce the penalty if you add a keep together
        if not utils.keep_NR_check(self, p, RouteDel.nodes2keep) and any(p[0] in e for e in RouteDel.nodes2keep):
            feasibility -= 1
            # time -= RouteDel.Data.Penalty
        '''

        return time

    def insert(self, i, seq, move_time):
        # will operate the insertion

        # Update the cost
        self.travel_time += move_time
        # The REAL insertion
        self.route.insert(i + 1, seq)
        # Update the nodes_in_path
        self.build_nodes()
        # redo the feasibility checks
        self.feasibility_check(RouteDel.Data)

    def remove(self, val=None, inx=None):
        if val:
            self.route.remove(val)
        if inx:
            del self.route[inx]

        # Update the nodes_in_path
        self.build_nodes()
        # Update the travel time of route
        self.calc_time(dis)
        self.feasibility_check(RouteDel.Data)

    def add_RDP(self, RDP):
        self.total_deliveries = sum(RDP)
        RDP_ID = max(self.RDP.keys()) + 1
        self.RDP[RDP_ID] = RDP
        return RDP_ID

    def set_RDP(self, RDP=None):
        # this function just used for the first time we want to set a RDP
        if RDP is not None:
            self.RDP[1] = RDP
        elif RouteDel.Class_RDP is not None:
            temp_RDP = [0] * RouteDel.Data.NN
            for n in self.route[:-1]:
                temp_RDP[n] = RouteDel.Class_RDP[n]
            self.RDP[1] = temp_RDP
        else:
            deliveries = np.array(list(nx.get_node_attributes(RouteDel.Data.G, 'demand').values())) * RouteDel.Data.C
            deliveries = np.floor(deliveries)
            RDP = [0] * RouteDel.Data.NN
            CAP = 0
            for n in self.route[0:-1]:
                # not include NN+1 in RDPs
                if deliveries[n] + CAP <= RouteDel.Data.Q:
                    RDP[n] = deliveries[n]
                    CAP += deliveries[n]
                else:
                    RDP[n] = 0
            self.RDP[1] = RDP

        self.total_deliveries = sum(self.RDP[1])

    def Is_unique(self, Col_dic):
        # 1 yes it is completely unique
        # 2 the RDP is unique
        # 3 noting is new
        indicator = 1
        inx = 0
        for inx, Col in Col_dic.items():
            if self.nodes_in_path == Col.nodes_in_path:
                if self.RDP[1] not in Col.RDP.values():
                    indicator = 2
                else:
                    indicator = 3
                return indicator, inx

        return indicator, inx+1

    @classmethod
    def E2keep(cls, edges):
        dic = {}
        cls.E2K = edges
        if edges:
            for i, j in edges:
                dic[i] = j
                dic[j] = i
        cls.edges2keep = dic
