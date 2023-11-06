"""
Created on Thu Sep 20 01:14:24 2018

@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""
from gurobipy import *
from itertools import *
import numpy as np
import sys
from os import path

BASEDIR = path.dirname(path.dirname(path.realpath(__file__)))
sys.path.append(BASEDIR)
import utils.utils as ut


def Time_Calc(Dis, R):
    Travelcost = 0
    PreNode = 0
    for n in R[1:-1]: # travel time calculation
        Travelcost += Dis[PreNode, n]
        PreNode = n
    return Travelcost
    
    
def routes_finder(X, NN):
    routes = []
    starters = [tub[1] for tub in X if tub[0] == 0]
    for st in starters:
        X.remove((0, st))
        current_node = st
        route = [0, st]
        while current_node != NN+1:
            tub = [tub for tub in X if current_node in tub][0]
            X.remove(tub)
            next_node = list(set(tub)-set([current_node]))
            route += next_node
            if len(next_node) == 0:
                ty = 0
            current_node = next_node[0]
        routes.append(route)
    return routes


def Model2(Data, R, SecondObjOnly=False, FirstObjOnly=False):
    NN = Data.NN
    M = Data.M
    Q = Data.Q
    G = Data.G
    Gc = Data.Gc
    Lambda = Data.Lambda
    Alpha = Data.Alpha
    Dis = Data.distances
    if FirstObjOnly:
        Gamma = 0
    else:
        Gamma = Data.Gamma
    assert (not (FirstObjOnly and SecondObjOnly))

    complement = [i for i in permutations(Gc.nodes, 2)] + [(0, i) for i in Gc.nodes] + [(i, NN+1) for i in Gc.nodes]
    
    TotalD = Data.total_demand
    
    Travel_time = list(Dis.values())
    BigM = sum(Travel_time)
    CF_MIP = Model("Two_Commodity_Flow ")
    
    x = CF_MIP.addVars(complement, lb=0, ub=1, name="x", vtype=GRB.BINARY)
    y = CF_MIP.addVars(complement, name="y")
    w = CF_MIP.addVars(complement, name="w")
    u = CF_MIP.addVars(G.nodes, name="u")
    v = CF_MIP.addVars(range(NN), name="v")#,vtype=GRB.INTEGER)

    CF_MIP.update()
    if SecondObjOnly:
        CF_MIP.setObjective( quicksum(Dis[i,j]*x[i,j] for i,j in x.keys() if j!=NN+1) )
    else:
        tp = CF_MIP.addVars(Gc.nodes, Gc.nodes, lb=0, name="tp")
        tn = CF_MIP.addVars(Gc.nodes, Gc.nodes, lb=0, name="tn")

        CF_MIP.setObjective(Alpha * quicksum(G.nodes[i]['demand'] - v[i] for i in Gc.nodes)
                        + (Lambda/TotalD) * quicksum(tp[i, j] + tn[i, j] for i, j in tp.keys())
                        - (Gamma/R) * (Data.Total_dis_epsilon-quicksum(Dis[i, j]*x[i, j] for i, j in x.keys() if j != NN+1)))
        CF_MIP.addConstrs(tp[i, j] - tn[i, j] ==
            v[j]*G.nodes[i]['demand'] - v[i]*G.nodes[j]['demand'] for i in Gc.nodes for j in Gc.nodes)
        if not FirstObjOnly:
            CF_MIP.addConstr(quicksum(Dis[i, j]*x[i, j] for i, j in complement if j != NN+1) <= Data.Total_dis_epsilon)

    CF_MIP.addConstrs(quicksum(w[i, j]-y[i, j] for j in G.nodes() if j != i and j != 0) +
                      quicksum(y[j, i]-w[j, i] for j in G.nodes() if j != i and j != NN+1) == 2*v[i] for i in Gc.nodes)
    
    CF_MIP.addConstr(quicksum(y.select(0, '*')) == quicksum(v))
    CF_MIP.addConstr(quicksum(w.select(0, '*')) == M*Q-quicksum(v))
    CF_MIP.addConstr(quicksum(w.select('*', NN+1)) == M*Q)
    
    CF_MIP.addConstrs(y[i, j] + w[i, j] == Q*x[i, j] for i, j in complement)
    
    CF_MIP.addConstrs(u[j] >= u[i]+Dis[i, j] + BigM*(x[i, j]-1) for i, j in complement)
    CF_MIP.addConstrs(u[i] <= Data.Maxtour for i in Gc.nodes)
    
    CF_MIP.addConstrs(v[i] <= G.nodes[i]['demand'] for i in Gc.nodes)

    CF_MIP.addConstr(quicksum(v) <= G.nodes[0]['supply'] )

    CF_MIP.addConstrs(quicksum(x[i, k] for i in G.nodes if i != k and i != NN+1) ==
                      quicksum(x[k, i] for i in G.nodes if i != k and i != 0) for k in Gc.nodes)
    CF_MIP.addConstrs(quicksum(x.select(i, '*')) == 1 for i in Gc.nodes)

    CF_MIP.update()
    #CF_MIP.Params.OutputFlag=0 
    #CF_MIP.write("IPmodel.lp")
    CF_MIP.params.TimeLimit = 600
    CF_MIP.params.MIPGap = 0.0001
    CF_MIP.optimize()
    Objval = -1000000
    absGini, GiniIndex, TT_Time = (0, 0, 0)
    if CF_MIP.status != 3:
        Xv = CF_MIP.getAttr('x', x)
        Vv = CF_MIP.getAttr('x', v)
        Uv = CF_MIP.getAttr('x', u)
        Tours = [b[0] for b in Xv.items() if b[1] > 0.5]
        Tours = routes_finder(Tours, NN)
        RDP = []
        VisitTime = []
        for tour in Tours:
            RDP.append([0]*NN)
            VisitTime.append([])
            demand = []
            for n in tour[1:-1]:
                RDP[-1][n] = Vv[n]
                VisitTime[-1].append(round(Uv[n], 1))
                demand.append(Data.G.nodes[n]["demand"])
            print(f"Vehicle demand :{demand} | Total: {sum(demand)}")
            print(tour)
            print(RDP[-1])
            # print((np.array(demand) - np.array(RDP[-1])) / np.array(demand))
            print("Total delivery : %s" % sum(RDP[-1]))
            print("The Tour length is : %s \n" %round(Time_Calc(Dis, tour),1) )
        absGini = ut.calculate_the_obj(Data, Tours, RDP)
        GiniIndex = ut.calculate_Gini_index(Data, RDP)
        TT_Time = sum([Time_Calc(Dis, r) for r in Tours])
        print(Vv)
        Total_unS = sum([G.nodes[n]['demand']  - Vv[n] for n in Vv])
    print(CF_MIP.objVal, CF_MIP.ObjBound, CF_MIP.Runtime,  CF_MIP.MIPGap)
    return CF_MIP.objVal, CF_MIP.ObjBound, CF_MIP.Runtime,  CF_MIP.MIPGap, absGini, TT_Time, GiniIndex, Total_unS