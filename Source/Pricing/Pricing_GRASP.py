"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""

import numpy as np
import pickle as Pick
import copy
from utils import Seq
from Pricing import Path


def Make_it_compatible(edges2keep, edges2avoid):
    edges2keep_dic = {}
    edges2avoid_dic = {}
    if edges2keep:
        for i, j in edges2keep:
            if i not in edges2keep_dic.keys():
                edges2keep_dic[i] = [j]
            else:
                edges2keep_dic[i].append(j)

            if j not in edges2keep_dic.keys():
                edges2keep_dic[j] = [i]
            else:
                edges2keep_dic[j].append(i)

    if edges2avoid:
        for i, j in edges2avoid:
            if i not in edges2avoid_dic.keys():
                edges2avoid_dic[i] = [j]
            else:
                edges2avoid_dic[i].append(j)

            if j not in edges2avoid_dic.keys():
                edges2avoid_dic[j] = [i]
            else:
                edges2avoid_dic[j].append(i)

    return edges2keep_dic, edges2avoid_dic


def Make_seq_compatible(seqs):
    new_seqs = {}
    for key, a_list in seqs.items():
        for a in a_list:
            if key == "D0" or key == "D1":
                new_seqs[tuple(a.string)] = a
            else:
                new_seqs[tuple(a.string)] = a
                new_seqs[tuple(a.string[::-1])] = Seq.Sequence(a.string[::-1])

    return new_seqs


def Node_value_calc(Data, Dual):
    # Note that this node value just account for the Pi1 and Pi5
    # Therefore these values should just be used in Quantity assignment directly
    # Since there we already decided on the nodes to be in the path and there sequence .
    # looking at Pi1 and Pi5 is just enough

    Pi1 = np.array(Dual[1])
    Pi5 = np.array(Dual[5])
    Values = {}
    for i in range(Data.NN-1):
        Values[i + 1] = - Pi5 - 1
        for j in range(Data.NN-1):
            Values[i + 1] -= (Pi1[i][j] - Pi1[j][i]) * Data.G.nodes[j+1]["demand"]

    return Values


# Algorithm functions
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


def constructive_alg(Data, All_seq, S_local):
    alpha = 0.8
    any_luck = 0
    NN = Data.NN
    # Initiate the sequences by creating a string for all.
    depot_sec = Seq.Sequence.check(All_seq, 0)
    if len(depot_sec) <= 1:
        current_path = Path.Path([All_seq[(0,)], All_seq[(NN + 1,)]])
    elif 1 < len(depot_sec) <= 2:
        print(depot_sec)
        current_path = Path.Path([depot_sec[0], All_seq[(NN + 1,)]])
        del S_local[tuple(depot_sec[0])]
    else:
        best_sec_with_depot = min(depot_sec[1:], key=lambda x: S_local[x])
        current_path = Path.Path([best_sec_with_depot, All_seq[(NN + 1,)]])
        for S in depot_sec[:-1]:
            del S_local[tuple(S)]

    while S_local.values() and any([a <= 0 for a in S_local.values()]):
        # find the vertex with maximum profit
        # print([a for a in S_local.values()])
        Min_inx = min(S_local.keys(), key=lambda x: S_local[x])
        Min_S = S_local[Min_inx]
        # build the randomized set
        RCL1 = [(i, a) for i, a in S_local.items() if a <= alpha * Min_S]
        # select one vertex to insert to the path
        inx = np.random.choice(range(len(RCL1)))
        (v, Sv) = RCL1[inx]

        # find the best insertion position for selected vertex
        move, move_value_change, move_time_change = current_path.Best_move(All_seq[v])

        del S_local[tuple(v)]

        # if possible insert the vertex to the route
        if move:
            (inx, nodes) = move
            seq = All_seq[nodes]
            current_path.insert(inx, seq, move_value_change, move_time_change)
            any_luck = 1
            # remove the selected vertex from further selections
            if len(move[1]) >= 2 and move[1][::-1] in S_local.keys():
                del S_local[move[1][::-1]]

    return current_path, any_luck


def exchange_operator(Data, All_seq, current_path):
    Current_value = current_path.value
    improvement = 0
    for inx, outward in enumerate(current_path.path[1:-1]):
        Moves_profile = {}
        inx += 1
        for inward in All_seq.values():
            # As soon as the inward is in the path already we won't do the exchange
            if inward in current_path.path or 0 in inward.string:
                pass
            else:
                # let's check if the reverse exist and is in the path
                rule = tuple(inward.string[::-1]) in All_seq.keys()
                if rule:
                    rule = All_seq[tuple(inward.string[::-1])] in current_path.path and len(inward.string) >= 2
                    # if the reverse exist and in the path we do the exchange when it is equal to the outward
                    rule = rule and inward.string[::-1] != outward.string

                # if the inward_revers is in the path and not equal to outward we have to pass (do nothing)
                # but if it is equal to outward we have to do the exchange
                if rule:  # if the reverse exist and equal to the outward
                    pass
                else:  # general situation
                    # check the avoided
                    if inward.string[0] in Path.Path.edges2avoid.keys():
                        if current_path.path[inx - 1].string[-1] not in Path.Path.edges2avoid[inward.string[0]]:
                            continue

                    if inward.string[-1] in Path.Path.edges2avoid.keys():
                        if current_path.path[inx + 1].string[-1] not in Path.Path.edges2avoid[inward.string[-1]]:
                            continue

                    time_change = current_path.exchange_time(inx, outward, inward)

                    if current_path.path_time + time_change <= Data.Maxtour:
                        Moves_profile[(inx, tuple(outward.string), tuple(inward.string))] = \
                            current_path.Changes_in_value(inx, inward, outward)[0]

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


def insertion_operator(All_seq, current_path):
    improvement = 0
    for inward in All_seq.values():
        if inward in current_path.path or 0 in inward.string:
            pass
        else:
            rule = tuple(inward.string[::-1]) in All_seq.keys()
            if rule:
                rule = All_seq[tuple(inward.string[::-1])] in current_path.path
            if rule:
                pass
            else:
                move, move_value_change, move_time_change = current_path.Best_move(inward)
                if move:
                    (inx, nodes) = move
                    seq = All_seq[nodes]
                    current_path.insert(inx, seq, move_value_change, move_time_change)
                    improvement = 1

    return current_path, improvement


def GRASP(Data, All_seq, edges2keep, edges2avoid, Duals, R):
    NN = Data.NN
    Path.Path.edges2keep, Path.Path.edges2avoid = Make_it_compatible(edges2keep, edges2avoid)
    All_seq = Make_seq_compatible(All_seq)
    Path.Path.All_seq = All_seq
    Path.Path.Data = Data
    Path.Path.dis = Data.distances
    Path.Path.Duals = Duals
    Path.Path.R = R
    # load the node scores
    Path.Path.Node_Value = Node_value_calc(Data, Duals)
    Pi6 = Duals[6]
    # Calculate the sequence values
    S = {}
    for key, sec in All_seq.items():
        if key != (0,) and key != (NN + 1,):
            # Since it just used in constructive alg then we account for pi3 as well
            S[key] = sum(
                [Path.Path.Node_Value[i] - Duals[3][i - 1] for i in sec.string if i != 0])

            # Adding the edge2keep duals
            for e in Pi6.keys():
                if e[0] in sec.string and e[1] in sec.string:
                    S[sec] += -Pi6[e]
            # However, we store the values for sequence just according to Pi1 and Pi5
            sec.value = sum([Path.Path.Node_Value[i] for i in sec.string if i != 0])

    #  Set of generated paths
    All_negative_paths = []
    N_O_route = np.random.choice([5, 10, 20])
    for _ in range(N_O_route):
        # print("--------------- GRASP next restart ----------------")
        # construct the initial path
        new_S = copy.deepcopy(S)
        current_path, any_luck = constructive_alg(Data, All_seq, new_S)

        if not any_luck:
            continue

        # current_path = Two_opt(current_path)

        improvement = 1
        counter = 0
        while improvement and counter < 10:
            if improvement and current_path.value < 0:
                # Keep a fixed number of columns to add
                if len(All_negative_paths) >= Data.N_Added_GRASP:
                    del All_negative_paths[0]
                    All_negative_paths.append(copy.deepcopy(current_path))
                else:
                    All_negative_paths.append(copy.deepcopy(current_path))
            # Improvement with local search
            # first stage "exchange"
            current_path, improvement1 = exchange_operator(Data, All_seq, current_path)
            # print(f"GRASP after exchange: {current_path.value}")
            # second stage "insertion"
            current_path, improvement2 = insertion_operator(All_seq, current_path)
            # print(f"GRASP after insertion: {current_path.value}")
            # current_path = Two_opt(current_path)
            improvement = improvement1 or improvement2
            counter += 1

    if len(All_negative_paths) == 0:
        return 0, None, 100

    return current_path.value < 0, All_negative_paths, current_path.value



