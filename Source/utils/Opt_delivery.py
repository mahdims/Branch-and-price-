"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""

from gurobipy import *
import numpy as np


def Opt_delivery(Data, Routes):
    Q = Data.Q
    G = Data.G
    Gc = Data.Gc
    Lambda = Data.Lambda
    TotalD = Data.total_demand
    LP = Model("Opt_del")

    tp = LP.addVars(Gc.nodes, Gc.nodes, lb=0, name="tp")
    tn = LP.addVars(Gc.nodes, Gc.nodes, lb=0, name="tn")
    q = LP.addVars(G.nodes, name="q")

    LP.update()
    LP.setObjective(quicksum(Gc.nodes[i]['demand'] - q[i] for i in Gc.nodes)
                     + (Lambda / TotalD) * quicksum(tp[i, j] + tn[i, j] for i, j in tp.keys()) )

    LP.addConstrs((tp[i, j] - tn[i, j] == q[i] * G.nodes[j]['demand'] - q[j] * G.nodes[i]['demand'] for i in Gc.nodes for j in Gc.nodes), name="linear")

    LP.addConstr(quicksum(q[i] for i in Gc.nodes) <= G.nodes[0]['supply'], name="Inv")

    LP.addConstrs(quicksum(q[i] for i in Gc.nodes if r.is_visit(i)) <= Q for r in Routes)

    LP.addConstrs(q[i] <= G.nodes[i]['demand'] for i in Gc.nodes)

    LP.Params.LogToConsole = 0
    LP.params.TimeLimit = 1500
    LP.Params.Threads = 1
    LP.update()
    LP.optimize()

    qv = LP.getAttr('x', q)

    RDP = {}
    for j, r in enumerate(Routes):
        RDP[j] = [0] * Data.NN
        for i in r.nodes_in_path:
            RDP[j][i] = round(qv[i], 10)
        print(f"Route {j}:", r.nodes_in_path)
        print(RDP[j])

    return LP.objVal, RDP


