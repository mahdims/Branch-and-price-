
from Node import Node
from feasibleSol import Initial_feasibleSol 
from Real_Input import Real_Input
import pickle as Pick
import time
import itertools as it
import numpy as np


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


    return

def read_object(filename):
    with open(filename, 'rb') as input:
        obj = Pick.load(input)
    return obj


def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)


def calculate_the_obj(Data, R, Routes,RDPs):
    Gc = Data.Gc
    # create the mapping to find the node quantities  :))
    Q_mapping = {}
    for i in Gc.nodes:
        for r_ID, route in enumerate(Routes):
            inx = np.where(np.array(route.route) == i)[0]
            if len(inx) != 0:
                inx = inx[0]
                break
        Q_mapping[i] = (r_ID,inx)

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


def branch_and_bound(Data, R, MaxTime):
    
    start = time.time()
    Node.Data = Data
    Node.R = R
    # Set initial Parameters
    Node.best_obj = 100000000000000000 # upper bound 
    Node.best_objtime = 0
    Gap = 100
    Elapsed_time = 0
    # Find the initial Columns
    Col_set, _ = Initial_feasibleSol(Data, Data.G)
    Col_dic = {}
    for inx, R_D in enumerate(Col_set):
            Col_dic[inx] = R_D  
    # make the root node
    root = Node(0, 0, 0, "center", Col_dic, Data.G)
    Node.LowerBound = round(root.Objval, 2)
    print("Start the BnP with root value %s" % Node.LowerBound )
    if root.integer(): # check if we need to continue
        Node.best_obj = round(root.Objval, 2)
        Node.best_node = root
        Node.best_Route = root.selected_route
        return (Node.best_node, Node.best_obj, Node.LowerBound, Node.best_objtime, Elapsed_time, Gap)

    # branch and create two fist nodes
    stack = root.Strong_Branching()

    ############# MAin loop #################
    while stack and Gap > 0.01 and Elapsed_time < MaxTime:
        print(f"Open nodes : {len(stack)}")
        node = min(stack, key=lambda i: i.Objval) # select the node with best objval


        Elapsed_time = round(time.time()-start,3)
        print("ID // Current objval // integer Objval // UB    // LB     // GAP // Elapsed T")
        print("%d     %s        %s          %s    %s   %s   %s"
            %(node.ID, round(node.Objval, 2), round(node.Int_Objval, 2), round(Node.best_obj, 2),
              round(Node.LowerBound, 2), Gap, Elapsed_time))

        print(sorted(stack, key=lambda x: x.Objval)[:4])

        stack.remove(node)

        if not node.feasible: # Fanthom by infeasibility
            print(f"Closed due to infeasiblity : Node {node.ID}")
            node.delete()
            continue
        # lower bound is the minmum obj among the un explored ones
        Node.LowerBound = node.Objval



        if node.Objval >= Node.best_obj: #Fanthom by bound
            print(f"Closed due to bound : Node {node.ID}")
            node.delete()
            continue

        if node.integer(): # Fanthom by integerity
            if node.Objval < Node.best_obj: # update upperbound
                Node.best_obj = node.Objval
                Node.best_objtime = round(time.time()-start, 3)
                Node.best_node = node

            print(f"Closed due to integrity : Node {node.ID}")
            node.delete()
            continue
        if node.Int_Objval < Node.best_obj:
             Node.best_obj = node.Int_Objval
             Node.best_objtime = round(time.time()-start, 3)
             Node.best_Route = node.Int_route
             Node.best_RDP = node.Int_RDP

        # select the branching rule and generates two child node
        child_nodes = node.Strong_Branching()
        stack += child_nodes
        #Node.Draw_the_tree()

        if Node.best_obj:
            Gap = round((Node.best_obj-Node.LowerBound)*100/Node.best_obj,3)
        else:
            Gap = None


        # for test to see if we calculate the objective currectly!
        Direct_Obj = calculate_the_obj(Data, R, Node.best_Route, Node.best_RDP)
        # print(Direct_Obj)

        node.delete()

    Gap = round((Node.best_obj - Node.LowerBound) * 100 / Node.best_obj, 3)
    print("Best sol    // LB  // time_2_best // Elapsed time // GAP")
    print(f"{round(Node.best_obj, 3)} //  {round(Node.LowerBound, 3)} //  {round(Node.best_objtime, 3)} // {Elapsed_time} // {Gap}")

    print_routes(Node.best_node)
    return Node.best_node, Node.best_obj, Node.LowerBound, Node.best_objtime, Elapsed_time, Gap
