"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""

import numpy as np
import networkx as nx
import sys


# This is the path object for use in pricing heuristics
class Path:
    R = 0
    All_seq = []
    edges2keep = None
    edges2avoid = None
    Connected_list = None
    Data = None
    dis = None
    Node_Value = None
    Duals = None

    def __init__(self, path):
        penalty2value = 0
        self.path = path
        self.value = 0
        PreNode = self.path[0]
        self.path_time = PreNode.string_time
        self.nodes_in_path = list(set(PreNode.string) - set([0]))
        for n in self.path[1:-1]:  # travel time calculation
            self.nodes_in_path += n.string
            # Add the distance between PreNode -- n
            self.path_time += Path.dis[PreNode.string[-1], n.string[0]] + n.string_time
            # Check if two sequence are allowed to be adjunct
            if Path.edges2avoid:
                if n.string[0] in Path.edges2avoid.keys():
                    if PreNode.string[-1] in Path.edges2avoid[n.string[0]]:
                        # we should add a huge penalty to the value
                        penalty2value = 1

            PreNode = n

        self.q = Quantities_assignment_new(Path.Data, Path.Node_Value, self.nodes_in_path)
        self.value = self.Calculating_path_value()
        if penalty2value:
            self.value += Path.Data.BigM_dis

    def where_in_path(self, v):
        for inx, a in enumerate(self.path):
            if v in a.string:
                return inx
        return None

    def check_if_all_have_del(self):
        for n in self.nodes_in_path:
            if self.q[n - 1] == 0.0:
                print("We found a node without delivery")

        Real_nodes_in_path = list(set(self.path[0].string) - set([0]))
        for n in self.path[1:-1]:
            Real_nodes_in_path += n.string

        if set(Real_nodes_in_path) != set(self.nodes_in_path):
            print("Problem with updating nodes_in_path in GRASP")

    def Calculating_path_value(self):
        gamma = Path.Data.Gamma
        d = np.array(list(nx.get_node_attributes(Path.Data.G, 'demand').values())[1:-1])
        Pi1 = np.array(Path.Duals[1])
        Pi2 = np.array(Path.Duals[2])
        Pi3 = np.array(Path.Duals[3])
        Pi4 = np.array(Path.Duals[4])
        Pi5 = np.array(Path.Duals[5])
        Pi6 = Path.Duals[6]

        a_var = np.zeros(Path.Data.NN - 1)
        if self.nodes_in_path:
            a_var[np.array(self.nodes_in_path) - 1] = 1

        Value = sum((-Pi1.dot(d) + d.dot(Pi1)) * self.q) - self.path_time * (Pi2 + gamma / Path.R) - Pi3.dot(a_var) \
            - Pi4 - (Pi5 + 1) * sum(self.q)
        # the dual variables added because of the edges 2 keep
        for e in Pi6.keys():
            inx = self.where_in_path(e[0])
            if inx is not None:
                if e[1] in self.path[inx].string:
                    Value -= Pi6[e]

        return Value

    def insertion_time(self, i, p):
        time = Path.dis[self.path[i].string[-1], p.string[0]] + Path.dis[p.string[-1], self.path[i + 1].string[0]] \
               + p.string_time - Path.dis[self.path[i].string[-1], self.path[i + 1].string[0]]

        # Adding the penalty cost for having an avoided edge
        if p.string[0] in Path.edges2avoid.keys():
            if self.path[i].string[-1] in Path.edges2avoid[p.string[0]]:
                time += Path.Data.BigM_dis
        if p.string[-1] in Path.edges2avoid.keys():
            if self.path[i + 1].string[0] in Path.edges2avoid[p.string[-1]]:
                time += Path.Data.BigM_dis

        return time

    def Best_move(self, v):
        current_value = self.value
        Candidate_dic = {}
        # create the candidate set for insertion
        CL = list(range(len(self.path) - 1))
        # eliminate the avoided nodes from candidate set
        if v.string[0] in Path.edges2avoid.keys():
            for avoid in Path.edges2avoid[v.string[0]]:
                inx = self.where_in_path(avoid)
                if inx is not None:
                    if self.path[inx].string[-1] == avoid:
                        CL.remove(inx)

        if v.string[-1] in Path.edges2avoid.keys():
            for avoid in Path.edges2avoid[v.string[-1]]:
                inx = self.where_in_path(avoid)
                if inx is not None:
                    if self.path[inx + 1].string[0] == avoid:
                        try:  # I am not sure about this
                            CL.remove(inx)
                        except KeyError:
                            pass

        for i in CL:
            time_change = self.insertion_time(i, v)
            if self.path_time + time_change <= Path.Data.Maxtour:
                Candidate_dic[(i, tuple(v.string))] = (self.Changes_in_value(i, v)[0], time_change)
        # select the move with the maximum decrease in path value
        if Candidate_dic.keys():
            selected_move = min(Candidate_dic.keys(), key=lambda x: Candidate_dic[x][0])
            if Candidate_dic[selected_move][0] <= current_value:
                return selected_move, Candidate_dic[selected_move][0], Candidate_dic[selected_move][1]

        return None, None, None

    def insert(self, inx, seq, move_value, move_time):
        # will operate the insertion
        # Update the cost
        self.path_time += move_time
        # Update the nodes_in_path
        self.nodes_in_path = self.nodes_in_path + seq.string
        # Update the path value
        self.value = move_value
        # The REAL insertion
        self.path.insert(inx + 1, seq)
        # Update the quantities
        self.q = Quantities_assignment_new(Path.Data, Path.Node_Value, self.nodes_in_path)

    def exchange_time(self, i, outward, inward):
        out = - outward.string_time + inward.string_time \
              - (Path.dis[self.path[i - 1].string[-1], outward.string[0]] +
                 Path.dis[outward.string[-1], self.path[i + 1].string[0]]) + \
              (Path.dis[self.path[i - 1].string[-1], inward.string[0]] +
               Path.dis[inward.string[-1], self.path[i + 1].string[0]])

        return out

    def Changes_in_value(self, i, inward, outward=None):

        gamma = Path.Data.Gamma
        d = np.array(list(nx.get_node_attributes(Path.Data.G, 'demand').values())[1:-1])
        Pi1 = np.array(Path.Duals[1])
        Pi2 = np.array(Path.Duals[2])
        Pi3 = np.array(Path.Duals[3])
        Pi4 = np.array(Path.Duals[4])
        Pi5 = np.array(Path.Duals[5])
        Pi6 = Path.Duals[6]
        a_var = np.zeros(Path.Data.NN - 1)

        if outward:  # it is an exchange
            new_node_list = self.nodes_in_path + inward.string
            for a in set(outward.string):
                new_node_list.remove(a)
            NewQ = Quantities_assignment_new(self.Data, Path.Node_Value, new_node_list)
            Total_time = self.path_time + self.exchange_time(i, outward, inward)

        else:  # this is an insertion
            new_node_list = self.nodes_in_path + inward.string
            NewQ = Quantities_assignment_new(self.Data, Path.Node_Value, new_node_list)
            Total_time = self.path_time + self.insertion_time(i, inward)

        # Calculate the value
        if new_node_list:
            a_var[np.array(new_node_list) - 1] = 1

        Total_value = sum((-Pi1.dot(d) + d.dot(Pi1)) * NewQ) - Total_time * (Pi2 + gamma / Path.R) - Pi3.dot(a_var) \
            - Pi4 - (Pi5 + 1) * sum(NewQ)
        # the dual variables added because of the edges 2 keep
        for e in Pi6.keys():
            if e[0] in new_node_list and e[1] in new_node_list:
                Total_value -= Pi6[e]
            if e[0] == 0 and e[1] in new_node_list:
                Total_value -= Pi6[e]

        # check if the avoided edges are here
        if Path.edges2avoid:
            try:
                Avoid_st = Path.edges2avoid[inward.string[0]]
            except KeyError:
                Avoid_st = []
            try:
                Avoid_ed = Path.edges2avoid[inward.string[-1]]
            except KeyError:
                Avoid_ed = []

            if outward:
                if self.path[i - 1].string[-1] in Avoid_st or self.path[i + 1].string[0] in Avoid_ed:
                    Total_value += Path.Data.BigM_dis
            else:
                if self.path[i].string[-1] in Avoid_st or self.path[i + 1].string[0] in Avoid_ed:
                    Total_value += Path.Data.BigM_dis

        return Total_value, NewQ

    def exchange(self, i, outward, inward):

        # the function will operate the exchange move, u
        # and update the N_of_nodes, path_time, keep_list, (avoid_list not included yet )
        outward = Path.All_seq[outward]
        inward = Path.All_seq[inward]
        self.value, self.q = self.Changes_in_value(i, inward, outward)
        self.path_time += self.exchange_time(i, outward, inward)
        # The actual exchange
        self.path = self.path[:i] + [inward] + self.path[i + 1:]
        # Updating the nodes in the path
        self.nodes_in_path += inward.string
        for a in outward.string:
            self.nodes_in_path.remove(a)


def Quantities_assignment_old(Data, Nodes_value, node_set):
    # if the set of nodes in the path is given like the way I defined this function. It works correctly.
    # But if I need to decide on which node is going to the path then i have to calculate the value*di + ph3 to decide
    # which node is going to the path
    # this function calculate the delivery quantities completely independent of the
    # sequences and minimize the reduced cost (negative)

    if 0 in node_set:
        print(node_set)
        sys.exit("0 in the route in Quantities_assignment -start ")

    remaining_Q = Data.Q
    G = Data.G
    q_heuristic = {}
    Values = {}
    for i in node_set:
        if i != 0 and i != Data.NN + 1:
            Values[i] = Nodes_value[i]
    while Values:
        next_2_assign = min(Values.keys(), key=lambda x: Values[x])  # most negative node value gets the
        if Values[next_2_assign] < 0:
            q_heuristic[next_2_assign] = min(remaining_Q, G.nodes[next_2_assign]["demand"])
            remaining_Q -= q_heuristic[next_2_assign]
        else:
            q_heuristic[next_2_assign] = 0
        del Values[next_2_assign]
    Out_q = np.zeros(Data.NN - 1, dtype=int)

    for inx, value in q_heuristic.items():
        Out_q[inx - 1] = value

    return Out_q


def Quantities_assignment_new(Data, Nodes_value, node_set):
    # Only for use in pricing algorithm
    # when the valid inequalities are added
    # According to reduced cost , known nodes to visit, most negative cost, Updated with prop1 and 2
    Out_q = np.zeros(Data.NN - 1, dtype=float)

    if len(node_set) == 0:
        return Out_q

    if 0 in node_set:
        print(node_set)
        sys.exit("0 in the route in Quantities_assignment -start ")

    q_heuristic = {}
    route_D = sum([Data.G.nodes[i]["demand"] for i in node_set])
    s_node = min(node_set, key=lambda i: Data.G.nodes[i]["demand"])

    if route_D * (Data.G.nodes[0]["supply"] / Data.total_demand) >= Data.Q:
        q_heuristic[s_node] = Data.G.nodes[s_node]["demand"] * float(Data.Q) / route_D

    else:
        modified_obj = sum([Nodes_value[i] * Data.G.nodes[i]["demand"] / Data.G.nodes[s_node]["demand"] for i in node_set])

        if modified_obj < 0:
            q_heuristic[s_node] = min(Data.G.nodes[s_node]["demand"],
                                      Data.G.nodes[s_node]["demand"] * float(Data.Q) / route_D)
        else:
            q_heuristic[s_node] = (Data.G.nodes[0]["supply"] / Data.total_demand) * Data.G.nodes[s_node]["demand"]

    for i in node_set:
        if i not in q_heuristic.keys():
            q_heuristic[i] = q_heuristic[s_node] * float(Data.G.nodes[i]["demand"] / Data.G.nodes[s_node]["demand"])

    for inx, value in q_heuristic.items():
        Out_q[inx - 1] = round(value, 6)

    return Out_q
