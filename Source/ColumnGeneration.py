import itertools as it
import networkx as nx
import numpy as np
import sys
from feasibleSol import Route
from itertools import *
from gurobipy import *
from Pricing_GRASP import GRASP, Quantities_assignment , Node_value_calc
import copy


def subtourelim(model, where):

    if where == GRB.callback.MIPSOL:
        selected = []
        sol = {}
        # make a list of edges selected in the solution
        for i, j in model._varX.keys():
            sol[i, j] = model.cbGetSolution(model._varX[i, j])
            if sol[i, j] > 0.5:
                selected.append((i, j))
        # find the shortest cycle in the selected edge list
        tour = Get_the_Subtours(G, selected)
        if tour:
            # add a subtour elimination constrain
            complement = [i for i in permutations(tour, 2)] # if just one node gives it will return empty list []
            complement2 = copy.copy(complement)
            for e in complement:
                if e not in model._varX.keys():
                    complement2.remove(e)

            expr1 = 0
            for i, j in complement2:
                expr1 += model._varX[i, j]
            for k in tour:
                expr2 = 0

                for l in tour:
                    if l != k:
                        expr2 += model._varA[l]

                model.cbLazy(expr1 <= expr2)

      
def Get_the_Subtours(G, edges):
    NN = G.number_of_nodes()-1
    nodes = set()
    for e in edges:
        nodes = nodes | set(e)
        
    Resulting_G = nx.Graph()
    Resulting_G.add_nodes_from(nodes)
 
    for e in edges:
        Resulting_G.add_edge(*e)
   
    subtours = [c for c in sorted(nx.connected_components(Resulting_G), key=len, reverse=True)]
    # Put the tour with depot nodes at first
    for s in subtours:
        if 0 in s and NN+1 in s:
            subtours.remove(s)
    if subtours:
        return list(subtours[subtours.index(min(subtours , key=lambda x :len(x) ) ) ]) # return minim length sub ture
    else:
        return []


def get_Duals(NN, RMP, edges2keep):
    AllMasterCons = RMP.getConstrs()
    AllDual = RMP.getAttr("Pi", AllMasterCons)
    linear = np.array(AllDual[0:(NN-1)*(NN-1)]).reshape((NN-1, NN-1)) #get_constraints(RMP, name='linear')
    Per_end = (NN-1)*(NN-1)
    totaltime = np.array(AllDual[Per_end])
    visit = np.array(AllDual[Per_end+1:Per_end+NN])
    Per_end = Per_end+NN
    vehicle = np.array(AllDual[Per_end])
    Inv = np.array(AllDual[Per_end+1])
    EdgK = {}
    if edges2keep:
        Per_end = (NN - 1) * (NN - 1) + NN + 2
        for i,e in enumerate(edges2keep):
            EdgK[e] = AllDual[Per_end:][i]
    
    return AllDual, linear, totaltime, visit, vehicle, Inv, EdgK


def Calculate_the_subproblem_obj(Data, R, Duals, col, q):
    gamma = Data.Gamma
    d = np.array(list(nx.get_node_attributes(Data.G, 'demand').values())[1:-1])
    Pi1 = np.array(Duals[1])
    Pi2 = np.array(Duals[2])
    Pi3 = np.array(Duals[3])
    Pi4 = np.array(Duals[4])
    Pi5 = np.array(Duals[5])
    Pi6 = Duals[6]
    a_var = np.zeros(Data.NN - 1)
    if col.route[1:-1]:
        a_var[np.array(col.route[1:-1]) - 1] = 1
    Value = sum((-Pi1.dot(d) + d.dot(Pi1)) * q) - col.travel_time * (Pi2 + gamma / R) - Pi3.dot(a_var) \
                - Pi4 - (Pi5 + 1) * sum(q)

    # the dual variables added because of the edges 2 keep
    for e in Pi6.keys():
        if e[0] in col.route and e[1] in col.route:
            Value -= Pi6[e]

    return Value


def Columns_with_negitive_costs(Data, R, Duals, Col_dic):
    indicator = 0
    All_new_cols_IDs = []
    Nodes_value = Node_value_calc(Data, Duals)
    for col_ID, col in Col_dic.items():
        NewQ = Quantities_assignment(Data, Nodes_value , col.route)
        # in GRASP  we only have the q for customers but here in ColGen node zero should have 0 delivery
        New_RDP = [0] + list(NewQ)
        Value = Calculate_the_subproblem_obj(Data,R,Duals,col,NewQ)
        if Value < -0.01 and New_RDP not in col.RDP.values():
            # print(Value)
            indicator = 1
            RDP_ID = col.add_RDP(New_RDP)
            All_new_cols_IDs.append( (col_ID, RDP_ID) )
    return indicator, Col_dic, All_new_cols_IDs


def Set_sub_obj(Data, R, Gc, dis, Duals, edges2keep, Sub, x, q, a):
    NN = len(a)-1
    (AllDual, linear, totaltime, visit, vehicle, Inv, E_keep) = Duals
    Gc = G.subgraph(range(1, NN))

    if edges2keep:
        Sub.setObjective(
            - quicksum((q[i]*Gc.nodes[j]['demand']-q[j]*Gc.nodes[i]['demand'])*linear[i-1, j-1] for i in Gc.nodes for j in Gc.nodes)
            - quicksum(a[i]*visit[i-1] for i in Gc.nodes)
            - quicksum(q)*(Inv+1)-vehicle
            - quicksum(x[i, j]*dis[(i, j)] for (i, j) in x.keys() if j != NN+1) * (totaltime + Data.Gamma/R)
            - quicksum((x[j, i])*val for (i, j), val in E_keep.items() if i != 0 and j != NN+1)
            - quicksum((x[i, j])*val for (i, j), val in E_keep.items())
            , GRB.MINIMIZE)
    else:
        Sub.setObjective(
            - quicksum((q[i]*Gc.nodes[j]['demand']-q[j]*Gc.nodes[i]['demand'])*linear[i-1,j-1] for i in Gc.nodes for j in Gc.nodes)
            - quicksum(x[i, j]*dis[(i, j)] for (i, j) in x.keys() if j != NN+1) * (totaltime + Data.Gamma/R)
            - quicksum(a[i]*visit[i-1] for i in Gc.nodes)
            - quicksum(q)*(Inv+1)-vehicle
            , GRB.MINIMIZE)
    
    return Sub


def build_the_route(Data, New_Route, dis):
    Edges = copy.copy(New_Route)
    PerNode = 0
    route = [0]
    while Edges:
        for e in Edges:
            if PerNode in e:
                break
        route.append(e[1])
        PerNode = e[1]
        Edges.remove(e)
    New_Route = Route(route, Data, dis)
    return New_Route


def Update_Master_problem(Gc, R, edges2keep, RMP, Col_dic, Col_ID, RDP_ID):
    # Step 1 : see what is new about this column
    # step 2 : add the approprite variable and index
    New_Route  = Col_dic[Col_ID]
    Selected_edges = []
    pre_node = 0
    for next_node in New_Route.route[1:-1]:
        Selected_edges.append((pre_node, next_node))
        pre_node = next_node
    #  Update the Master problem  ##
    col = Column()
    try:
        for i, j in it.permutations(Gc.nodes(), 2):
            # Master problem linear constraint update ##
            cons = RMP.getConstrByName("linear[%d,%d]" % (i, j))
            col.addTerms(- New_Route.RDP[RDP_ID][j] * Gc.nodes[i]['demand'] + New_Route.RDP[RDP_ID][i] * Gc.nodes[j]['demand'], cons)

        for n in New_Route.route[1:-1]:
            consvisit = RMP.getConstrByName("visit[%d]" % n)
            col.addTerms(1, consvisit)

    except:
        print("can not add the column")
    # total time epsilon constraint ##
    cons = RMP.getConstrByName("Total_time")
    col.addTerms(New_Route.travel_time, cons)
    # vehicle constraint ###
    cons = RMP.getConstrByName("vehicle")
    col.addTerms(1, cons)
    # Inv constraint ###
    cons = RMP.getConstrByName("Inv")
    col.addTerms(sum(New_Route.RDP[RDP_ID]), cons)
    # edges 2 keep
    for i, j in edges2keep:
        cons = RMP.getConstrByName("edge2keep[%d,%d]" % (i, j))
        col.addTerms((i, j) in Selected_edges or (j, i) in Selected_edges, cons)

    RMP.addVar(lb=0, ub=1, obj=-sum(New_Route.RDP[RDP_ID]) - Gamma * New_Route.travel_time/R, name="y[%d,%d]" % (Col_ID,RDP_ID),
               column=col)

    return RMP


def Delete_the_unused_columns(RMP, Col_dic):
    Y = dict([(int(var.VarName.split('[')[1].split(']')[0]), var.X) for var in RMP.getVars() if var.VarName.find('y') != -1])
    for key,val in Y.items():
        if val == 0:
            del Col_dic[key]
            RMP.delVar(key)

    return RMP, Col_dic


def Get_the_Y_variables(RMP):
    Y = {}
    for var in RMP.getVars():
        if var.VarName.find('y') != -1:
            indexes = var.VarName.split('[')[1].split(']')[0].split(",")
            Y[int(indexes[0]), int(indexes[1])] = var.X

    return Y


def ColumnGen(Data, R, RMP, G_in, Col_dic, dis, edges2keep, edges2avoid, SubModel):
    (Sub, x, q, a) = SubModel
    Stoping_R_cost = -0.001
    heuristic_path_value = -10
    global G,Gamma
    G = G_in
    NN = Data.NN
    Gc = Data.Gc
    Gamma = Data.Gamma
    RMP_objvals = [] # A list to have all objvals
    # Set variables to start the main loop ###
    Subobj = -1
    counter = 0 # we move onb to the optimal solver when 3 sccesive heuristic can't improve the problem.
    Hit_the_Zero = 0 # the first time that the heuristic find a solution with value zero we use the optimal solver only
    Pre_Sub_obj = -10
    Heuristic_works = 1
    Solved_by_Heuristic = 0
    RMP_objvals.append(133)
    ############ Main loop ##########
    while Subobj < Stoping_R_cost:
        # Solve the Master problem
        RMP.optimize() 
        if RMP.status != 2:
            # Report that the problem in current node is infeasible
            print("Infeasible Master Problem")
            return 0, Data.BigM, [], Col_dic
        print("Master Problem Optimal Value: %f" %RMP.objVal)
        RMP_objvals.append(RMP.objVal)
        # Get the dual variables
        Duals = get_Duals(NN, RMP, edges2keep)
        # Solve Sub Problem
        # First search for the negative value columns and then  if you can not find any move on to the other approaches.
        # First we try the heuristics and then if the obj function found to be zero by then it is time to run
        # the optimal solver.
        # For each existing routes in the col set we calculate the delivery quantity by the heuristic approach.
        we_found_cols, Col_dic, All_new_cols_IDs = Columns_with_negitive_costs(Data, R, Duals, Col_dic)
        # RMP, Col_dic = Delete_the_unused_columns(RMP, Col_dic)
        if we_found_cols == 1:
            Solved_by_Heuristic = 0

        if not we_found_cols or not Heuristic_works:

            if Heuristic_works: # Solve it with the heuristics
                # First try to solve it with the heuristics and then if not a chance to find a solution
                (Heuristic_works, heuristic_paths, heuristic_path_value) = GRASP(Data, edges2keep, edges2avoid, Duals, R)
                Solved_by_Heuristic = Heuristic_works

            if not Heuristic_works:  # Solve it with mathematical model
                # Set the sub problem  objective
                Sub = Set_sub_obj(Data, R, Gc, dis, Duals, edges2keep, Sub, x, q, a)
                Sub.optimize(subtourelim)
                Subobj = Sub.objVal
                if Sub.status != 2: sys.exit("infeasible sub problem by model")
                # get the sub-problem solution
                Xv = Sub.getAttr('x',x)
                qv = Sub.getAttr('x',q)
                # create the new route - delivery ####
                Selected_edges = [e for e, value in Xv.items() if value > 0.5]
                New_Route = build_the_route(Data, Selected_edges, dis)
                New_RDP = np.zeros(NN)

                New_RDP[New_Route.route[1:-1]] = [qv[i] for i in New_Route.route[1:-1]]

                New_Route.set_RDP(list(New_RDP))

                Solved_by_Heuristic = 0
                Heuristic_works = 1 # by default next time heuristic should be able to solve the problem
                print("Sub Problem optimal value: %f" % Subobj)

        # update the counter in case that the heuristic can find different solution we run the exact sub problem.
        if 1.1 * Pre_Sub_obj <= heuristic_path_value <= 0.9 * Pre_Sub_obj:
            counter += 1
            # print(counter)
        else:
            counter = 0

        if counter >= 3:
            counter = 0
            Heuristic_works = 0
        # update the previous heuristic value
        Pre_Sub_obj = heuristic_path_value

        if heuristic_path_value > Stoping_R_cost:
            heuristic_path_value = -10
            Heuristic_works = 0 # change to 0 after the experiments

        if Subobj > Stoping_R_cost:
            continue

        # Add the new col and update the master problem
        if we_found_cols:
            for Col_ID, RDP_ID in All_new_cols_IDs:
                # Update the master problem with new columns
                RMP = Update_Master_problem(Gc, R, edges2keep, RMP, Col_dic, Col_ID,RDP_ID)

        if Solved_by_Heuristic:
            for path in heuristic_paths:
                Output_path = []
                for strings in path.path:
                    Output_path += strings.string
                New_Route = Route(Output_path, Data, dis)
                New_Route.set_RDP([0] + list(path.q))
                # check whether the new route is unique or not
                indicator, Col_ID = New_Route.Is_unique(Col_dic)
                if indicator == 1:
                    RDP_ID = 1
                    Col_dic[Col_ID] = New_Route
                elif indicator == 2:
                    RDP_ID = Col_dic[Col_ID].add_RDP(New_Route.RDP[1])
                else:
                    continue
                # Update the master problem with new columns
                RMP = Update_Master_problem(Gc, R, edges2keep,RMP,Col_dic, Col_ID, RDP_ID)

        elif not Solved_by_Heuristic and not we_found_cols: # Then it solved by sub problem mathematical model
            # check whether the new route is unique or not
            indicator, Col_ID = New_Route.Is_unique(Col_dic)
            if indicator == 1:
                RDP_ID = 1
                Col_dic[Col_ID] = New_Route
            elif indicator == 2:
                RDP_ID = Col_dic[Col_ID].add_RDP(New_Route.RDP[1])

            RMP = Update_Master_problem(Gc, R, edges2keep, RMP, Col_dic, Col_ID, RDP_ID)

    # read the final selected Y variables
    Y = Get_the_Y_variables(RMP)
    # print("Master Problem Optimal Value: %f" %RMP.objVal)
    return 1, RMP_objvals[-1], Y, Col_dic
