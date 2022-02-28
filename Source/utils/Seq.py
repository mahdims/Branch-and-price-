import sys
import networkx as nx
# This class group the nodes that should be together because of the edges to keep.
# I use this instead of a single node in every route/ path object


class Sequence:
    dis = None
    G = None
    Data = None

    def __init__(self, string):
        self.string = string
        self.string_time = 0
        self.start = string[0]
        self.end = string[-1]
        self.value = 0
        self.demand = sum([Sequence.G.nodes[i]['demand'] for i in string])
        self.delivery = None
        self.AngleWithDepot = Sequence.G.nodes[string[0]]["AngleWithDepot"]
        # Calculate the time of string
        if len(self.string) >= 2:
            PreNode = self.string[0]
            for n in self.string[1:]:  # travel time calculation
                self.string_time += self.dis[PreNode, n]
                PreNode = n
        else:
            self.string_time = 0

        self.set_initial_deliveries(Sequence.Data)

    def __getitem__(self, key):
        try:
            return self.string[key]
        except KeyError:
            sys.exit(f"KeyError: There is no {key} in the string with length{len(self.string)}")

    def __len__(self):
        return len(self.string)

    def __repr__(self):
        return f"seq {self.string}"

    def set_initial_deliveries(self, Data):
        self.delivery = self.demand * Data.C

    @classmethod
    def check(cls, All_seq, n):
        # This method check if the given node is in any of the strings and if yes then it will return the list
        # contains it. It can be a one-member list or more, including the node itself.

        # depot can be in more than one sequence
        if n == 0:
            outs = []
            for s in All_seq.values():
                if 0 in s.string:
                    outs.append(s)
            return outs

        for obj in All_seq.values():
            if n in obj.string:
                return obj
        return None


def select_starting_edge(depot_list):
    # this function select the seq s that have depot inside first . if only seq with depot is there it returns that one
    for seq in depot_list:
        if len(seq) > 1:
            depot_list.remove(seq)
            return depot_list, seq

    if len(depot_list) == 1:
        return depot_list, depot_list[0]
    else:
        return [], None


def Create_seq(Data, edges2keep):
    # This function will figure out the real node sequences
    # All_seq has three category of nodes "D0" the depot and "N" normal nodes and "D1" the auxilary depot
    # note that "D0" can have more than one member
    Sequence.G = Data.G
    Sequence.Data = Data
    All_seq = {}
    Con_G = nx.Graph()
    for i, a in edges2keep.items():
        for j in a:
            Con_G.add_edge(i, j)
    Connected_list = [list(a) for a in nx.connected_components(Con_G)]
    # Since the sequence of connection is important here we try to find the right one.
    for inx, node_sets in enumerate(Connected_list):

        if len(node_sets) >= 3:
            end_points = []
            for n in node_sets:
                if len(edges2keep[n]) == 1:
                    end_points.append(n)
            Connected_list[inx] = list(nx.all_simple_paths(Con_G, end_points[0], end_points[1]))[0]
    # Build all of the sequences.
    All_seq["D0"] = []
    for a in Connected_list:
        if 0 not in a:
            All_seq[tuple(a)] = [Sequence(a)]
            All_seq[tuple(a)].append(Sequence(a[::-1]))
        elif a[0] == 0:
            All_seq["D0"].append(Sequence(a))
        else:
            depot_inx = a.index(0)
            All_seq["D0"].append(Sequence(a[:depot_inx+1][::-1]))
            All_seq["D0"].append(Sequence(a[depot_inx:]))
    for a in range(1, Data.NN):
        if a not in edges2keep.keys():
            All_seq[a] = [Sequence([a])]

    All_seq["D0"].append(Sequence([0]))
    All_seq["D1"] = [Sequence([Data.NN + 1])]

    return All_seq, Connected_list

