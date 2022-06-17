"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""

from gurobipy import *
import numpy as np
import sys
from itertools import *


def SubProblem(Data, G, dis, edges2keep=None, edges2avoid=None):
    NN = Data.NN
    Q = Data.Q
    Gc = Data.Gc
    # all edges possible now (except xi0 and x8i )
    complement = [i for i in permutations(Gc.nodes, 2)] + [(0, i) for i in Gc.nodes] + [(i, NN+1) for i in Gc.nodes]

    if edges2avoid:
        for i, j in edges2avoid:
            if i == 0:
                complement.remove((i, j))
            else:
                complement.remove((i, j))
                complement.remove((j, i))

    Sub = Model("Sub Problem")
    x = Sub.addVars(complement, name="x", vtype=GRB.BINARY)
    a = Sub.addVars(Gc.nodes, name="a", vtype=GRB.BINARY)
    q = Sub.addVars(Gc.nodes, name="q", vtype=GRB.CONTINUOUS)
    z = Sub.addVar(name="z", vtype=GRB.BINARY)
    Sub.update()
    Sub._varX = x
    Sub._varA = a
    Sub._varQ = q
    Sub._varPsi = {}

    if edges2keep:
        for i, j in edges2keep:
            if i == 0:
                Sub.addConstr(x[0, j] == a[j])
            elif j == 0:
                Sub.addConstr(x[0, i] == a[i])
            else:
                Sub.addConstr(x[i, j] + x[j, i] == a[i])
                Sub.addConstr(a[i] == a[j])

    Sub.addConstr(quicksum(x[i, j]*dis[(i, j)] for (i, j) in complement if j != NN+1) <= Data.Maxtour)
    Sub.addConstr(quicksum(x.select(0, "*")) == 1)
    Sub.addConstr(quicksum(x.select("*", NN+1)) == 1)
    Sub.addConstrs(quicksum(x.select("*", i)) == quicksum(x.select(i, "*")) for i in Gc.nodes)
    Sub.addConstrs(quicksum(x.select(i, "*")) == a[i] for i in Gc.nodes)
    Sub.addConstrs(q[i] <= G.nodes[i]['demand']*a[i] for i in Gc.nodes)
    # demand proportional distribution
    Sub.addConstrs(q[i] * G.nodes[j]['demand'] <= q[j] * G.nodes[i]['demand'] +
                   G.nodes[i]['demand'] * G.nodes[j]['demand'] * (1 - a[j]) for i in Gc.nodes for j in Gc.nodes if i != j)
    # Prop 2 and Alg 1 implications
    Sub.addConstr(quicksum(G.nodes[i]['demand'] * a[i] for i in Gc.nodes) * (G.nodes[0]['supply'] / Data.total_demand)
                  <= Q + G.nodes[0]['supply'] * (1-z))

    Sub.addConstr(quicksum(q) >= Q - Q*z)

    Sub.addConstr(quicksum(Gc.nodes[i]['demand'] * a[i] * (
                G.nodes[0]['supply'] / Data.total_demand) for i in Gc.nodes) - G.nodes[0]['supply'] * (1-z) <= quicksum(q))

    Sub.addConstr(quicksum(q) <= Q)

    Sub.Params.OutputFlag = 0
    Sub.params.LazyConstraints = 1
    Sub.params.TimeLimit = int(1.5 * Data.NN)
    Sub.params.MIPGapAbs = 0.0000001
    return Sub


def check_sub_sol_is_feasible(Sub, RouteDel, RDP):
    Sub.reset(0)

    p_n = 0
    for n in RouteDel.nodes_in_path:
        Sub._varX[p_n, n].lb = 1
        p_n = n
        Sub._varA[n].lb = 1

    for n_inx, q in enumerate(RDP):
        if n_inx ==0  : continue
        Sub._varQ[n_inx].lb = q
        Sub._varQ[n_inx].ub = q

    Sub.update()

    return Sub


def check_constrints(Gc, RouteDel, RDP):
    check = {}
    for i in Gc.nodes:
        for j in Gc.nodes:
            if i != j:
                check[(i,j)] = RDP[i] * Gc.nodes[j]['demand'] <= RDP[j] * Gc.nodes[i]['demand'] + Gc.nodes[i]['demand'] * \
                             Gc.nodes[j]['demand'] * (1 - RouteDel.is_visit(j) != -1)
    if not all(check.values()):
        stop =0