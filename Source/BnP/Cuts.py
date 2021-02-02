import time
from gurobipy import *


def violation_value(cut, Columns, Ys):
    violation = 0
    cut = list(cut)
    for r_ID, r in Columns.items():
        # first we check if two nodes of cut set are in the route
        if r.is_visit(cut[0]) + r.is_visit(cut[1]) + r.is_visit(cut[2]) >= 2:
            violation += sum([Ys[(r_ID, i)] for i in range(1, len(r.RDP))])

    return violation - 1


def separation_subrow(Data, Columns, Ys, per_cut_set):
    node_route = {}

    for node in range(1, Data.NN+1):
        node_route[node] = {"with": [], "without": []}
        for r_ID, r in Columns.items():
            if 0 < sum([Ys[(r_ID, i)] for i in range(1, len(r.RDP))]) < 1:
                if r.is_visit(node):
                    node_route[node]["with"].append(r_ID)
                else:
                    node_route[node]["without"].append(r_ID)

    # start = time.time()
    all_cut_set = []
    all_cut_set2 = [cut[0] for cut in per_cut_set]
    for node in range(1, Data.NN+1):

        for r in node_route[node]["without"]:

            for second_node in Columns[r].nodes_in_path:

                for second_route in node_route[node]["with"]:

                    if second_node in Columns[second_route].nodes_in_path:

                        for n in Columns[second_route].nodes_in_path:

                            if n != node and n != second_node:
                                cut = set((node, second_node, n))

                                if cut not in all_cut_set2:
                                    all_cut_set2.append(cut)
                                    all_cut_set.append([cut, violation_value(cut, Columns, Ys)])

    all_cut_set = sorted(all_cut_set, key=lambda x: x[1], reverse=True)
    # print(f"Number of columns: {len(Columns)}")
    # print(f"Separation took : {time.time()-start} sec")
    return [a for a in all_cut_set[:15] if a[1] > 0]


def update_master_subrow_cuts(RMP, Columns, N_of_cuts, cuts):
    counter = N_of_cuts - len(cuts)
    for cut in cuts:
        cut = list(cut[0])
        exper = 0
        for r, q in RMP._varY.keys():
            route = Columns[r]
            if route.is_visit(cut[0]) + route.is_visit(cut[1]) + route.is_visit(cut[2]) >= 2:
                exper += RMP._varY[r, q]

        RMP.addConstr(exper <= 1, name="Subrow[%d]" % counter)
        counter += 1
    return RMP


def update_subproblem_with_cuts(Sub, N_of_cuts, cuts):
    inx_of_cuts = list(range(N_of_cuts - len(cuts), N_of_cuts))
    psi = {}
    for inx in inx_of_cuts:
        psi[inx] = Sub.addVar(name=f"psi{inx}", vtype=GRB.BINARY)

    Sub._varPsi.update(psi)

    for g, cut in enumerate(cuts):
        Sub.addConstr(quicksum(Sub._varA[i] for i in cut[0]) <= 1 + 2*psi[inx_of_cuts[g]])

    return Sub