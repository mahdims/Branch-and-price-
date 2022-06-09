import time
import itertools as it
import numpy as np
from utils import Seq, utils
from BnP.Node import Node
from os import path
import heapq


def print_routes(node):

    if node:
        selected = [key for key, val in node.Y.items() if val > 0.9]

        for r,d in selected:
            print("\n")
            print(node.Col_dic[r].route)
            print(node.Col_dic[r].RDP[d])
            if node.Int_route:
                if node.Col_dic[r] not in node.Int_route:
                    print("This is not the int route")

    else:
        for ID, route in enumerate(Node.best_Route):
            print("\n")
            print(route.route)
            print(Node.best_RDP[ID])


def calculate_the_obj(Data, R, Routes, RDPs):
    Gc = Data.Gc
    # create the mapping to find the node quantities  :))
    Q_mapping = {}
    for i in Gc.nodes:
        for r_ID, route in enumerate(Routes):
            inx = np.where(np.array(route.route) == i)[0]
            if len(inx) != 0:
                inx = inx[0]
                break
        Q_mapping[i] = (r_ID, inx)

    big_RDP = [0]
    for i in Gc.nodes:
        (r_ID, inx) = Q_mapping[i]
        big_RDP.append(RDPs[r_ID][inx])

    part1 = 0
    for i in Gc.nodes:
        (r_ID, inx) = Q_mapping[i]
        part1 += Gc.nodes[i]['demand'] - RDPs[r_ID][inx]

    part2 = 0
    for i, j in it.product(Gc.nodes, Gc.nodes):
        (r_IDi, inxi) = Q_mapping[i]
        (r_IDj, inxj) = Q_mapping[j]
        part2 += abs(Gc.nodes[j]['demand']*RDPs[r_IDi][inxi] - Gc.nodes[i]['demand']*RDPs[r_IDj][inxj])

    part2 = (Data.Lambda / Data.total_demand) * part2
    part3 = Data.Gamma * (Data.Total_dis_epsilon - sum([r.travel_time for r in Routes])) / R

    return(part1+part2+part3)


def print_updates(start, Filename):
    # @TODO please update the results saving directory when nessecary.
    # print(f"Open nodes : {len(stack)}")
    Elapsed_time = round(time.time() - start, 3)
    print("LB       // UB       // GAP   //Elapsed T // Time_2_best")
    print(f"{round(Node.LowerBound, 2)}\t{round(Node.UpperBound, 2)}\t{Node.Gap}\t{Elapsed_time}\t{Node.time2UB}")

    results = [Node.LowerBound, Node.UpperBound, Node.Gap, Node.time2UB, Elapsed_time]
    BASE_DIR = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
    utils.write_log(results, f"{BASE_DIR}/Data/Results/{Filename}.txt", Node.best_Route, Node.best_RDP)


def branch_and_bound(Data, MaxTime, Filename):
    
    start = time.time()
    Node.Data = Data
    Node.R = Data.R
    Node.MaxTime = MaxTime + time.time()
    # Set initial Parameters
    Node.best_objtime = 0
    Gap = 100
    Elapsed_time = 0
    # Initial lower bound
    Node.LowerBound = Data.total_demand - Data.G.nodes[0]["supply"]

    nodes2keep = {"N": {}, "E": []}
    nodes2avoid = {"N": {}, "E": []}

    # Find the initial Columns
    Data.All_seq, _, _ = Seq.Create_seq(Data, {})

    # make the root node
    root = Node(0, 0, 0, "center", {}, Data.G, nodes2keep=nodes2keep, nodes2avoid=nodes2avoid)
    # Stack is the pool of feasible BnB nodes
    stack = [root]
    heapq.heapify(stack)
    Node.LB_UB_GAP_update(stack, root, start)

    print("Start the BnP with root value %s" % Node.LowerBound)
    if root.integer(): # check if we need to continue
        print_updates(start, Filename)
        UB, LB, time2UB, Gap = Node.UpperBound, Node.LowerBound, Node.time2UB, Node.Gap
        return str(round(UB,3)), str(round(LB,3)), str(round(Gap,3)), str(round(time2UB,3)), str(round(Elapsed_time,3)), str(Node.NodeCount)

    while len(stack) and Node.Gap >= 0.009999999 and Elapsed_time < MaxTime:

        Elapsed_time = round(time.time() - start, 3)

        print_updates(start, Filename)

        # best first search strategy
        print([(n.level, n.ID, round(n.lower_bound, 3)) for n in heapq.nsmallest(4, stack)])
        node = heapq.heappop(stack)

        # Fathom by bound
        if node.lower_bound >= Node.UpperBound:
            print(f"Closed due to bound : Node {node.ID}")
            node.delete()
            continue

        # Fathom by integrity
        if node.integer():
            Node.LB_UB_GAP_update(stack, node, start)
            print(f"Closed due to integrity : Node {node.ID}")
            node.delete()
            continue

        child_nodes = node.Strong_Branching()

        if Node.infeasible_master:
            break

        for child in child_nodes:
            if not child.feasible:
                print(f"Node {child.ID} pruned by infeasibility")
            elif child.lower_bound >= Node.UpperBound:
                print(f"Node {child.ID} pruned by bound")
            else:
                heapq.heappush(stack, child)
                Node.LB_UB_GAP_update(stack, child, start)

        # Node.Draw_the_tree()
        # Direct_Obj = calculate_the_obj(Data, R, Node.best_Route, Node.best_RDP)
        # print(Direct_Obj)

        node.delete()

    print_updates(start, Filename)

    Elapsed_time = round(time.time() - start, 3)
    UB, LB, time2UB, Gap = Node.UpperBound, Node.LowerBound, Node.time2UB, Node.Gap

    return str(round(UB,3)), str(round(LB,3)), str(round(Gap,3)), str(round(time2UB,3)), str(round(Elapsed_time,3)), str(Node.NodeCount)
