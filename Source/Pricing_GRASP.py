import numpy as np
from Real_Input import Real_Input
import pickle as Pick
import copy
import networkx as nx
import itertools as it
## Necessary functions
def Make_it_compatible(edges2keep, edges2avoid):
    edges2keep_dic = {}
    edges2avoid_dic = {}
    for i,j in edges2keep:
        if i not in edges2keep_dic.keys():
            edges2keep_dic[i] = [j]
        else:
            edges2keep_dic[i].append(j)

        if j not in edges2keep_dic.keys():
            edges2keep_dic[j] = [i]
        else:
            edges2keep_dic[j].append(i)

    for i,j in edges2avoid:
        if i not in edges2avoid_dic.keys():
            edges2avoid_dic[i] = [j]
        else:
            edges2avoid_dic[i].append(j)

        if j not in edges2avoid_dic.keys():
            edges2avoid_dic[j] = [i]
        else:
            edges2avoid_dic[j].append(i)

    return edges2keep_dic , edges2avoid_dic


def Node_value_calc(Data, Dual):
    d = np.array(list(nx.get_node_attributes(Data.G, 'demand').values())[1:-1])
    Pi1 = np.array(Dual[1])
    Pi5 = np.array(Dual[5])

    nominator = Pi1.dot(d)
    dominator = np.array(d.dot(Pi1), dtype=float)
    Values = {}
    for inx, a in enumerate(nominator):
        if a > 0:
            if dominator[inx] > 0:
                Values[inx + 1] = a - dominator[inx] + Pi5 +1
            else:
                Values[inx + 1] = a + abs(dominator[inx]) + Pi5 +1
        else:
            if dominator[inx] < 0:
                Values[inx + 1] = abs(dominator[inx]) - abs(a) + Pi5 +1
            else:
                Values[inx + 1] = - abs(a) - dominator[inx] + Pi5 +1

    return Values


def Quantities_assignment(Data, Nodes_value , node_set):
    # if the set of nodes in the path is given like the way I defined this function. It works correctly.
    # But if I need to decide on which node is going to the path then i have to calculate the value*di + ph3 to decide
    # which node is going to the path
    # this function calculate the delivery quantities completely independent from the sequences
    remaining_Q = Data.Q
    G = Data.G
    q_heuristic = {}
    Values={}
    for i in node_set:
        if i !=0 and i != Data.NN+1:
            Values[i] = Nodes_value[i]
    while Values:
        next_2_assign = max(Values.keys(), key=lambda x: Values[x])
        if Values[next_2_assign] >= 0:
            q_heuristic[next_2_assign] = min(remaining_Q, G.nodes[next_2_assign]["demand"])
            remaining_Q -= q_heuristic[next_2_assign]
        else:
            q_heuristic[next_2_assign] = 0
        del Values[next_2_assign]
    Out_q = np.zeros(Data.NN - 1)

    for inx, value in q_heuristic.items():
        Out_q[inx-1] = value

    return Out_q


def Connected_Graph(Data, edges2keep):
    # This function will figure out the seqences real node sequences
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
    for a in Connected_list:
        if 0 not in a:
            sequence(a)
            sequence(a[::-1])
        elif a[0] == 0:
            sequence(a)
        else:
            depot_inx = a.index(0)
            sequence(a[:depot_inx+1][::-1])
            sequence(a[depot_inx:])
    for a in range(Data.NN):
        if a not in edges2keep.keys():
            sequence([a])
    sequence([Data.NN + 1])

    return Connected_list


## Classes
class Path:
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
                        penalty2value= 1


            PreNode = n

        self.q = Quantities_assignment(Path.Data, Path.Node_Value ,self.nodes_in_path)
        self.value = self.Calculating_path_value()
        if penalty2value:
            self.value += Path.Data.BigM_dis

    def where_in_path(self, v):
        for inx, a in enumerate(self.path):
            if v in a.string:
                return inx
        return None

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
            a_var[np.array(self.nodes_in_path)-1] = 1

        Value = sum((-Pi1.dot(d) + d.dot(Pi1))*self.q) - self.path_time * (Pi2 + gamma / Path.R) - Pi3.dot(a_var) \
                - Pi4 - (Pi5 + 1) * sum(self.q)
        # the dual variabls added because of the edges 2 keep
        for e in Pi6.keys():
            inx = self.where_in_path(e[0])
            if inx is not None:
                if e[1] in self.path[inx].string:
                    Value -= Pi6[e]

        return Value

    def insertion_time(self, i, p):
        time = Path.dis[self.path[i].string[-1], p.string[0]] + Path.dis[p.string[-1], self.path[i + 1].string[0]] \
                   + p.string_time - Path.dis[self.path[i].string[-1], self.path[i + 1].string[0]]

        # Adding the penalty cost for having an avoid ing edge
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
        # eliminate the avoid nodes from candidate set
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
                    if self.path[inx+1].string[0] == avoid:
                        try: # I am not sure about this
                            CL.remove(inx)
                        except:
                            pass

        for i in CL:
            time_change = self.insertion_time(i,v)
            if self.path_time + time_change <= Path.Data.Maxtour:
                Candidate_dic[(i, tuple(v.string))] = (self.Changes_in_value(i, v)[0], time_change)
        # select the move with the maximum decrease in path value
        if Candidate_dic.keys():
            selected_move = min(Candidate_dic.keys(), key=lambda x: Candidate_dic[x][0])
            if Candidate_dic[selected_move][0] <= current_value :
                return selected_move, Candidate_dic[selected_move][0], Candidate_dic[selected_move][1]

        return None, None ,None

    def insert(self, move, move_value, move_time):
        # will operate the insertion
        (i, inserties) = move
        # Finding the insertion seqeunce
        inserties = sequence.All_sec[inserties]
        # Update the cost
        self.path_time += move_time
        # Update the nodes_in_path
        self.nodes_in_path = self.nodes_in_path + inserties.string
        # Update the path value
        self.value = move_value
        # The REAL inseartion
        self.path.insert(i + 1, inserties)
        # Update the quantities
        self.q = Quantities_assignment(Path.Data, Path.Node_Value, self.nodes_in_path)

    def exchange_time(self, i, outward, inward):
        out = - outward.string_time + inward.string_time \
              - (Path.dis[self.path[i - 1].string[-1], outward.string[0]] + \
                 Path.dis[outward.string[-1], self.path[i + 1].string[0]]) + \
                (Path.dis[self.path[i - 1].string[-1], inward.string[0]] + \
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
        a_var = np.zeros(Path.Data.NN-1)

        if outward: # it is an exchange
            #sec_set = copy.copy(self.path)
            #sec_set.remove(outward)
            #sec_set += [inward]
            new_node_list = self.nodes_in_path + inward.string
            for a in set(outward.string):
                new_node_list.remove(a)
            NewQ = Quantities_assignment(self.Data, Path.Node_Value, new_node_list)
            Total_time = self.path_time + self.exchange_time(i, outward, inward)


        else: # this is an insertation
            new_node_list = self.nodes_in_path + inward.string
            NewQ = Quantities_assignment(self.Data, Path.Node_Value, new_node_list)
            Total_time = self.path_time + self.insertion_time(i, inward)

        # Calculate the value
        if new_node_list:
            a_var[np.array(new_node_list) - 1] = 1

        Total_value = sum((-Pi1.dot(d) + d.dot(Pi1)) * NewQ) - Total_time * (Pi2 + gamma / Path.R) - Pi3.dot(a_var)\
                      - Pi4 - (Pi5 + 1) * sum(NewQ)
        # the dual variabls added because of the edges 2 keep
        for e in Pi6.keys():
            if e[0] in new_node_list and e[1] in new_node_list:
                Total_value -= Pi6[e]
            if e[0] == 0 and e[1] in new_node_list:
                Total_value -= Pi6[e]

        # check if the avoid edges are here
        if Path.edges2avoid:
            try:
                Avoid_st = Path.edges2avoid[inward.string[0]]
            except:
                Avoid_st = []
            try:
                Avoid_ed = Path.edges2avoid[inward.string[-1]]
            except:
                Avoid_ed = []

            if outward:
                if self.path[i-1].string[-1] in Avoid_st or self.path[i+1].string[0] in Avoid_ed:
                    Total_value += Path.Data.BigM_dis
            else:
                if self.path[i].string[-1] in Avoid_st or self.path[i+1].string[0] in Avoid_ed:
                    Total_value += Path.Data.BigM_dis

        return Total_value, NewQ

    def exchange(self, i, outward, inward):

        # the function will operate the exchange move, u
        # and update the N_of_nodes, path_time, keep_list, (avoid_list not included yet )
        outward = sequence.All_sec[outward]
        inward = sequence.All_sec[inward]
        self.value, self.q = self.Changes_in_value(i, inward, outward)
        self.path_time += self.exchange_time(i, outward, inward)
        # The actual exchange
        self.path = self.path[:i] + [inward] + self.path[i + 1:]
        # Updating the nodes in the path
        self.nodes_in_path += inward.string
        for a in outward.string:
            self.nodes_in_path.remove(a)


class sequence:
    dis = None
    edges2avoid = None
    All_sec = {}

    def __init__(self, string):
        self.string = string
        self.string_time = 0
        self.start = string[0]
        self.endpoint = string[-1]
        self.value = 0
        # Calculate the time of string
        if len(self.string) >= 2:
            PreNode = self.string[0]
            for n_inx, n in enumerate(self.string[1:]):  # travel time calculation
                self.string_time += self.dis[PreNode, n]
                PreNode = n
        else:
            self.string_time = 0

        sequence.All_sec[tuple(string)] = self

    @classmethod
    def check(cls, n):
        # This method check if the given node is in any of the strings and if yes then it will return the list
        # contains it. It can be a one-member list or more including the node itself.
        if n == 0 : # depot can be in more than one sequence
            outs= []
            for s in cls.All_sec.values():
                if 0 in s.string:
                    outs.append(s)
            return outs

        for obj in cls.All_sec.values():
            if n in obj.string:
                return obj
        return None

    @classmethod
    def reset(cls):
        cls.All_sec={}


## Algorithm functions
def swap_2opt(Broute, i, k):
    route = Broute.path
    assert 0 < i < (len(route) - 1)
    assert i < k < len(route)
    new_route = route[0:i]
    new_route.extend(reversed(route[i:k + 1]))
    new_route.extend(route[k + 1:])
    assert len(new_route) == len(route)
    return Path(new_route)


def Two_opt(route):
    # improves an existing route using the 2-opt swap until no improved route is found
    improvement = True
    best_route = route
    best_distance = route.path_time
    while improvement:
        improvement = False
        for i in range(1, len(best_route.path) - 1):
            for k in range(i + 1, len(best_route.path) - 1):
                new_route = swap_2opt(best_route, i, k)
                if new_route.path_time < best_distance:
                    best_distance = new_route.path_time
                    best_route = new_route
                    improvement = True
                    break
                    # improvement found, return to the top of the while loop
                if improvement:
                    break

        assert len(best_route.path) == len(route.path)
    return best_route


def constructive_alg(Data, S_local):
    alpha = 0.2
    any_luck = 0
    NN = Data.NN
    # Initiate the sequences by creating an string for all.
    if (0,) in sequence.All_sec.keys():
        current_path = Path([sequence.All_sec[(0,)], sequence.All_sec[(NN + 1,)]])
    else:
        sec = sequence.check(0)
        if len(sec)<=1 :
            current_path = Path([sec[0], sequence.All_sec[(NN + 1,)]])
            del S_local[sec[0]]
        else:
            best_sec_with_depot = min(sec, key=lambda x: S_local[x])
            current_path = Path([best_sec_with_depot, sequence.All_sec[(NN + 1,)]])
            for S in sec:
                del S_local[S]

    move_cost = 0
    while S_local.values() and any([a <= 0 for a in S_local.values()]):
        # find the vertex with maximum profit
        Min_inx = min(S_local.keys(), key=lambda x: S_local[x])
        Min_S = S_local[Min_inx]
        # build the randomized set
        RCL1 = [(i, a) for i, a in S_local.items() if  a <= alpha * Min_S]
        # select one vertex to insert to the path
        inx = np.random.choice(range(len(RCL1)))
        (v, Sv) = RCL1[inx]
        if v in current_path.path:
            hh = 0
        if any([n in current_path.nodes_in_path for n in v.string]):
            hh = 0
        # find the best insertion position for selected vertex
        move, move_value_change ,move_time_change = current_path.Best_move(v)
        # if possible insert the vertex to the route
        if move:
            current_path.insert(move, move_value_change, move_time_change)
            any_luck = 1
        # remove the selected vertex from further selections
        del S_local[v]
        try:
            del S_local[sequence.All_sec[move[1][::-1]]]
        except:
            pass

    return current_path, any_luck


def exchange_operator(Data, current_path):
    Current_value = current_path.value
    improvement = 0
    for inx, outward in enumerate(current_path.path[1:-1]):
        Moves_profile = {}
        inx += 1
        for inward in sequence.All_sec.values():
            if inward in current_path.path or 0 in inward.string: # As soon as the inward is in the path already we won't do the exchange
                pass
            else:
                # let's check if the reverse exist and is in the path
                rule = tuple(inward.string[::-1]) in sequence.All_sec.keys()
                if rule:
                    rule = sequence.All_sec[tuple(inward.string[::-1])] in current_path.path and len(inward.string) >=2
                    # if the reverse exist and in the path we do the exchange when it is equal to the outward
                    rule = rule and inward.string[::-1] != outward.string

                # if the inward_revers is in the path and not equal to outward we have to pass (do nothing)
                # but if it is equal to outward we have to do the exchange
                if rule:  # if the reverse exist and equal to the outward
                    pass
                else:  # general situation
                    # check the avoid
                    if inward.string[0] in Path.edges2avoid.keys():
                        if current_path.path[inx - 1].string[-1] not in Path.edges2avoid[inward.string[0]]:
                            continue

                    if inward.string[-1] in Path.edges2avoid.keys():
                        if current_path.path[inx + 1].string[-1] not in Path.edges2avoid[inward.string[-1]]:
                            continue

                    time_change = current_path.exchange_time(inx, outward, inward)

                    if current_path.path_time + time_change <= Data.Maxtour:
                        Moves_profile[(inx, tuple(outward.string), tuple(inward.string))] = current_path.Changes_in_value(
                            inx, inward, outward)[0]

            # decide on which move to operate
        if Moves_profile.keys():
            selected_move = min(Moves_profile.keys(), key=lambda x: Moves_profile[x])
            move_value = Moves_profile[selected_move]
            if move_value < Current_value:
                current_path.exchange(*selected_move)
                improvement = 1
            elif 0:
                possible_options = [a for a in Moves_profile.items() if a[1][0] == 0]
                # select the one that have a minimum traveling time
                best_option = min(possible_options, key=lambda x: x[1][1])
                if best_option[1][1] < 0:
                    print(best_option)
                    current_path.exchange(best_option[0])
                    improvement = 1
            else:
                pass

    return current_path, improvement


def insertion_operator(current_path):
    improvement = 0
    for inward in sequence.All_sec.values():
        if inward in current_path.path or 0 in inward.string:
            pass
        else:
            rule = tuple(inward.string[::-1]) in sequence.All_sec.keys()
            if rule:
                rule = sequence.All_sec[tuple(inward.string[::-1])] in current_path.path
            if rule:
                pass
            else:
                move, move_value_change ,move_time_change = current_path.Best_move(inward)
                if move:
                    current_path.insert(move, move_value_change, move_time_change)
                    improvement = 1

    return current_path, improvement


def GRASP(Data, edges2keep, edges2avoid, Duals,R):
    NN = Data.NN
    edges2keep , edges2avoid = Make_it_compatible(edges2keep , edges2avoid)
    Path.edges2keep = edges2keep
    Path.edges2avoid = edges2avoid
    Path.Data = Data
    Path.dis = Data.distances
    Path.Duals = Duals
    Path.R=R
    sequence.dis = Data.distances
    sequence.edges2avoid = edges2avoid
    Connected_Graph(Data, edges2keep)
    # load the node scores
    # Note that this node value just account for the Pi1 and Pi5 Therfore these values should just be used in Quantity assignemnt directly
    # Since there we already decided on the nodes to be in the path and there sequence .looking at Pi1 and Pi5 is just enough
    Path.Node_Value = Node_value_calc(Data, Duals)
    Pi6 = Duals[6]
    # Calculate the sequence values
    S = {}
    for key, sec in sequence.All_sec.items():
        if key != (0,) and key != (NN + 1,):
            # Since it just used in constructive alg then we account for pi3 as well
            S[sec] = sum(
                [-1*Path.Node_Value[i] * min(Data.G.nodes[i]["demand"], Data.Q) - Duals[3][i - 1] for i in sec.string if i!=0])
            # Adding the edge2keep duals
            for e in Pi6.keys():
                if e[0] in sec.string and e[1] in sec.string:
                    S[sec] += -Pi6[e]
            # However we store the values for sequence just according to Pi1 and Pi5
            sec.value = sum([Path.Node_Value[i] for i in sec.string if i !=0])

    # construct the initial path
    current_path, any_luck = constructive_alg(Data, S)
    if not any_luck:
        sequence.reset()
        return (0, None, None)
    # current_path = Two_opt(current_path)

    # Set of generated paths
    All_negitive_paths = []
    improvement = 1
    while improvement:
        if improvement and current_path.value < 0 :
            All_negitive_paths.append(copy.copy(current_path))
        # Improvement with local search
        # first stage "exchange"
        current_path, improvement1 = exchange_operator(Data, current_path)
        # second stage "insertion"
        current_path, improvement2 = insertion_operator(current_path)
        # current_path = Two_opt(current_path)
        improvement = improvement1 or improvement2

    sequence.reset()
    return current_path.value < 0, All_negitive_paths, current_path.value