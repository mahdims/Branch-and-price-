import itertools as it
import networkx as nx
import numpy as np
import sys
from Column_Gen import Sub_model
from utils import utils
from utils import Route_delivery as RD
from itertools import *
from gurobipy import *
from Pricing import Pricing_GRASP as PR
from Pricing import Path
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
            complement = [i for i in it.permutations(tour, 2)]  # if just one node gives it will return empty list []
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
    NN = G.number_of_nodes() - 1
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
        if 0 in s and NN + 1 in s:
            subtours.remove(s)
            break

    if subtours:
        return list(min(subtours, key=lambda x: len(x)))  # return minim length sub ture
    else:
        return []


def get_Duals(NN, RMP):
    AllMasterCons = RMP.getConstrs()
    AllDual = RMP.getAttr("Pi", AllMasterCons)
    linear = np.array(AllDual[0:(NN - 1) * (NN - 1)]).reshape((NN - 1, NN - 1))  # get_constraints(RMP, name='linear')
    Per_end = (NN - 1) * (NN - 1)
    totaltime = np.array(AllDual[Per_end])
    visit = np.array(AllDual[Per_end + 1:Per_end + NN])
    Per_end = Per_end + NN
    vehicle = np.array(AllDual[Per_end])
    Inv = np.array(AllDual[Per_end + 1])
    EdgK = {}
    Per_end += 2
    # if edges2keep["E"]:
    #    for i, e in enumerate(edges2keep["E"]):
    #        EdgK[e] = AllDual[Per_end:Per_end+len(edges2keep["E"])][i]

    sub_row = []
    # TODO I should check the correctness of the following Duals, is indexing correct?
    if RMP.getConstrByName("Subrow[0]"):
        # Per_end = Per_end + len(edges2keep["E"])
        sub_row = np.array(AllDual[Per_end:])
        # print(f"Dual of the sub row cuts: {sub_row}")
    return [], linear, totaltime, visit, vehicle, Inv, EdgK, sub_row


def Set_sub_obj(Data, R, Gc, dis, Duals, Sub):
    # @TODO The sub problem objective miscalculates !!!!!!!! Not for all solutions but for some solutions!

    Sub.reset(0)

    NN = Data.NN
    (_, linear, totaltime, visit, vehicle, Inv, E_keep, sub_row) = Duals

    expr = - quicksum(Sub._varQ[i] * (1 + Inv + quicksum(
        (linear[i - 1, j - 1] - linear[j - 1, i - 1]) * Gc.nodes[j]["demand"] for j in Gc.nodes)) for i in Gc.nodes) \
        - quicksum(Sub._varX[i, j] * dis[(i, j)] for (i, j) in Sub._varX.keys() if j != NN + 1) * (totaltime + Data.Gamma / R) \
        - quicksum(Sub._varA[i] * visit[i - 1] for i in Gc.nodes) \
        - vehicle

    '''
    for (i, j) in edges2keep["E"]:
        if i == 0:
            expr -= x[i, j] * E_keep[(i, j)]
        else:
            expr -= (x[i, j] + x[j, i]) * E_keep[(i, j)]
    '''
    # if Sub._varPsi:
    #    expr -= quicksum(Sub._varPsi[i] * sub_row[i] for i in Sub._varPsi.keys())

    Sub.setObjective(expr, GRB.MINIMIZE)
    Sub.update()
    return Sub


def Calculate_the_subproblem_obj(Data, R, Duals, col, q, cuts):
    gamma = Data.Gamma
    d = np.array(list(nx.get_node_attributes(Data.G, 'demand').values())[1:-1])
    Pi1 = np.array(Duals[1])
    Pi2 = np.array(Duals[2])
    Pi3 = np.array(Duals[3])
    Pi4 = np.array(Duals[4])
    Pi5 = np.array(Duals[5])
    Pi6 = Duals[6]  # keep edge duals
    Pi7 = Duals[7]  # sub row duals
    a_var = np.zeros(Data.NN - 1)
    if col.nodes_in_path:
        a_var[np.array(col.nodes_in_path) - 1] = 1
    Value = sum((- Pi1.dot(d) + d.dot(Pi1)) * q) - col.travel_time * (Pi2 + gamma / R) - Pi3.dot(a_var) - \
        Pi4 - (Pi5 + 1) * sum(q)

    # the dual variables added because of the edges 2 keep
    for e in Pi6.keys():
        if e[0] == 0 and e[1] in col.nodes_in_path:
            Value -= Pi6[e]
        elif e[0] in col.nodes_in_path and e[1] in col.nodes_in_path:
            Value -= Pi6[e]

    # Duals for subrow cuts
    for id, cut in enumerate(cuts):
        cut = list(cut[0])
        if (cut[0] in col.nodes_in_path) + (cut[1] in col.nodes_in_path) + (cut[2] in col.nodes_in_path) >= 2:
            Value -= Pi7[id]

    return Value


def Columns_with_negitive_costs(Data, R, Duals, Col_dic, cuts):
    indicator = 0
    All_new_cols_IDs = []
    Nodes_value = PR.Node_value_calc(Data, Duals)
    for col_ID, col in Col_dic.items():
        # Calculate Q for the problem with valid inequality
        NewQ = Path.Quantities_assignment_new(Data, Nodes_value, col.nodes_in_path)
        # in GRASP  we only have the q for customers but here in ColGen node zero should have 0 delivery
        New_RDP = [0] + list(NewQ)
        Value = Calculate_the_subproblem_obj(Data, R, Duals, col, NewQ, cuts)
        if Value < -1 and New_RDP not in col.RDP.values():
            # print(Value)
            indicator = 1
            RDP_ID = col.add_RDP(New_RDP)
            All_new_cols_IDs.append((col_ID, RDP_ID))
    return indicator, Col_dic, All_new_cols_IDs


def Update_Master_problem(Gc, R, cuts, RMP, Col_dic, Col_ID, RDP_ID):
    # Step 1 : see what is new about this column
    # step 2 : add the appropriate variable and index
    New_Route = Col_dic[Col_ID]
    Selected_edges = []
    pre_node = 0
    for next_node in New_Route.nodes_in_path:
        Selected_edges.append((pre_node, next_node))
        pre_node = next_node
    #  Update the Master problem  ##
    col = Column()

    for i, j in it.permutations(Gc.nodes(), 2):
        # Master problem linear constraint update ##
        cons = RMP.getConstrByName("linear[%d,%d]" % (i, j))
        col.addTerms(
            - New_Route.RDP[RDP_ID][j] * Gc.nodes[i]['demand'] + New_Route.RDP[RDP_ID][i] * Gc.nodes[j]['demand'], cons)

    for n in New_Route.nodes_in_path:
        consvisit = RMP.getConstrByName("visit[%d]" % n)
        col.addTerms(1, consvisit)

    # total time epsilon constraint
    cons = RMP.getConstrByName("Total_time")
    col.addTerms(New_Route.travel_time, cons)
    # vehicle constraint
    cons = RMP.getConstrByName("vehicle")
    col.addTerms(1, cons)
    # Inv constraint
    cons = RMP.getConstrByName("Inv")
    col.addTerms(sum(New_Route.RDP[RDP_ID]), cons)
    # edges 2 keep
    # for i, j in edges2keep["E"]:
    #    cons = RMP.getConstrByName("edge2keep[%d,%d]" % (i, j))
    #    col.addTerms(((i, j) in Selected_edges or (j, i) in Selected_edges)*1, cons)
    # Sub-row constraint
    for inx, cut in enumerate(cuts):
        cut = list(cut[0])
        if (cut[0] in New_Route.nodes_in_path) + (cut[1] in New_Route.nodes_in_path) + (
                cut[2] in New_Route.nodes_in_path) >= 2:
            cons = RMP.getConstrByName("Subrow[%d]" % inx)
            col.addTerms(1, cons)

    new_y = RMP.addVar(lb=0, ub=1, obj=-sum(New_Route.RDP[RDP_ID]) - Gamma * New_Route.travel_time / R,
                       name="y[%d,%d]" % (Col_ID, RDP_ID), column=col)

    RMP.update()
    RMP._varY.update({(Col_ID, RDP_ID): new_y})

    return RMP


def Delete_the_unused_columns(RMP, Col_dic):
    # TODO this function is not in use anymore and have to be adopted before back to operation
    Y = Get_the_Y_variables(RMP)
    for key, val in Y.items():
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


def Get_alternative_sols(Data, Sub):
    # @TODO Currently, we only get one solution out of GUROBI for pricing , We might take more than one
    # this function will return second and more worse solution after solving the pricing MIP
    # get the sub-problem solution
    MIPSolutions = []
    for sol_num in [0]:  # range(Sub.SolCount):
        Sub.Params.SolutionNumber = sol_num
        Selected_edges = []
        for key, var in Sub._varX.items():
            if var.Xn > 0.9:
                Selected_edges.append(key)
        New_Route, node_route = utils.build_the_route(Data, Edges=Selected_edges)
        if 0 in node_route[1:-1] or Data.NN + 1 in node_route[1:-1]:
            print(node_route)
            print("!!!!!!!!! Incorrect route !!!!!! \n Generated by the MIP sub problem \n Escaped we are safe")
            continue

        New_RDP = [0] * Data.NN
        for key, var in Sub._varQ.items():
            New_RDP[key] = var.xn
        New_Route.set_RDP(New_RDP)

        MIPSolutions.append(New_Route)
    return MIPSolutions


def create_new_columns(Data, R, All_seq, nodes2keep, nodes2avoid, Duals, Col_dic,Gc, dis, Sub,  cuts):
    # First, we create new delivery for existing routes in hope of finding reduce negative columns.
    # If not successful we run the GRASP heuristic
    # If not successful we run the Gurobi on pricing mathematical model
    flag = ''
    All_new_cols_IDs = []
    we_found_cols, Col_dic, All_new_cols_IDs = Columns_with_negitive_costs(Data, R, Duals, Col_dic, cuts)

    if we_found_cols:
        flag = "RECALC"
        return flag, Col_dic, All_new_cols_IDs, 10
    else:
        # Next, we try the GRASP heuristic
        (Heuristic_works, heuristic_paths, heuristic_path_value) = PR.GRASP(Data, All_seq, nodes2keep,
                                                                                nodes2avoid, Duals, R)
        # if the GRASP sol is too week just consider as non success
        if Heuristic_works:
            if all([path.value> -0.01 for path in heuristic_paths]):
                Heuristic_works = 0

        if Heuristic_works:
            flag = "GRASP"
            for path in heuristic_paths:
                New_Route = RD.RouteDel(path.path, "GRASP")
                New_Route.set_RDP([0] + list(path.q))
                # check whether the new route is unique or not
                indicator, Col_ID = New_Route.Is_unique(Col_dic)
                if indicator == 1:
                    RDP_ID = 1
                    Col_dic[Col_ID] = New_Route
                    All_new_cols_IDs.append((Col_ID,RDP_ID ))
                elif indicator == 2:
                    RDP_ID = Col_dic[Col_ID].add_RDP(New_Route.RDP[1])
                    All_new_cols_IDs.append((Col_ID, RDP_ID))
                else:
                    continue

            return flag, Col_dic, All_new_cols_IDs, -10

        else:
            # Next Solve it with mathematical model
            Sub = Set_sub_obj(Data, R, Gc, dis, Duals, Sub)
            Sub.optimize(subtourelim)
            if Sub.status != 2:
                # @TODO What that even means? is the node infeasible?
                sys.exit("infeasible sub problem by model")
            flag = "GUROBI"
            print("Sub Problem optimal value: %f" % Sub.objVal)
            MIP_solutions = Get_alternative_sols(Data, Sub)
            for New_Route in MIP_solutions:
                indicator, Col_ID = New_Route.Is_unique(Col_dic)
                if indicator == 1:
                    RDP_ID = 1
                    Col_dic[Col_ID] = New_Route
                    All_new_cols_IDs.append((Col_ID, RDP_ID))
                elif indicator == 2:
                    RDP_ID = Col_dic[Col_ID].add_RDP(New_Route.RDP[1])
                    All_new_cols_IDs.append((Col_ID, RDP_ID))
                else:
                    continue
            return flag, Col_dic, All_new_cols_IDs, Sub.objVal


def ColumnGen(Data, All_seq, R, RMP, G_in, Col_dic, dis, nodes2keep, nodes2avoid, Sub, cuts):
    Stoping_R_cost = -0.0002
    global G, Gamma
    G = G_in
    NN = Data.NN
    Gc = Data.Gc
    Gamma = Data.Gamma
    RMP_objvals = []
    Subobj = -1
    RMP_objvals.append(133)
    tail_counter = 0

    while Subobj < Stoping_R_cost and tail_counter < 1000:
        # STEP1: Solve the Master problem
        SolvedBy = ""
        RMP.reset()
        RMP.optimize()
        RMP.write("Master0.lp")
        if RMP.status != 2:
            # Report that the problem in current node is infeasible
            print("Infeasible Master Problem")
            sys.exit()
            return 0, RMP, Data.BigM, [], Col_dic
        RMP_objvals.append(RMP.objVal)
        print("Master Problem Optimal Value: %f" % RMP.objVal)

        # @TODO this is to cut the tail effect in CG but should we use it?
        if RMP_objvals[-1] * 0.99 <= RMP.objVal <= RMP_objvals[-1] * 1.01 \
                and SolvedBy == "GUROBI":
            tail_counter += 1
        else:
            tail_counter = 0

        # STEP2: Get the master problem duals
        Duals = get_Duals(NN, RMP)

        # STEP3: Find the reduced cost columns
        SolvedBy, Col_dic, All_new_cols_IDs, Subobj = \
            create_new_columns(Data, R, All_seq, nodes2keep, nodes2avoid, Duals, Col_dic, Gc, dis, Sub, cuts)
        # RMP, Col_dic = Delete_the_unused_columns(RMP, Col_dic)

        if Subobj > Stoping_R_cost and SolvedBy == "GUROBI":
            continue

        # STEP4: Add the new cols and update the master problem
        for Col_ID, RDP_ID in All_new_cols_IDs:
            RMP = Update_Master_problem(Gc, R, cuts, RMP, Col_dic, Col_ID, RDP_ID)
            # print(f"Out of {len(MIP_solutions)} columns {old_count} were already there.")

    if RMP.status != 2:
        RMP.optimize()

    Y = Get_the_Y_variables(RMP)
    # print("Master Problem Optimal Value: %f" %RMP.objVal)
    return 1, RMP, RMP_objvals[-1], Y, Col_dic
