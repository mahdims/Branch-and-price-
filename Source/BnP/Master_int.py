from gurobipy import *
import numpy as np


def Master_int(Data, R, CutOff, Col_dic):
    M = Data.M
    Q = Data.Q
    G = Data.G
    Gc = Data.Gc
    Lambda = Data.Lambda
    Gamma = Data.Gamma
    TotalD = Data.total_demand
    IMP = Model("Int Master")
        
    y = IMP.addVars(Col_dic.keys(), name="y", vtype=GRB.BINARY)
    tp = IMP.addVars(Gc.nodes, Gc.nodes, lb=0, name="tp")
    tn = IMP.addVars(Gc.nodes, Gc.nodes, lb=0, name="tn")
    q = IMP.addVars(G.nodes, name="q")
    inx = []
    for k in Col_dic.keys():
        for i in Col_dic[k].nodes_in_path:
            inx.append((i, k))
            
    Qr = IMP.addVars(inx, name="q")
    IMP.update()
    IMP.setObjective(quicksum(Gc.nodes[i]['demand'] - q[i] for i in Gc.nodes)
                    + (Lambda/TotalD) * quicksum(tp[i, j]+tn[i, j] for i, j in tp.keys())
                    + (Gamma/R) * (Data.Total_dis_epsilon-quicksum(Col_dic[r].travel_time*y[r] for r in Col_dic.keys())))
    
    IMP.addConstrs(Qr[i, r] <= q[i] for i in G.nodes for r in Col_dic.keys() if i in Col_dic[r].nodes_in_path)
    IMP.addConstrs(Qr[i, r] <= G.nodes[i]['demand']*y[r] for i in G.nodes for r in Col_dic.keys() if i in Col_dic[r].nodes_in_path)
    IMP.addConstrs(Qr[i, r] >= q[i]-G.nodes[i]['demand']*(1-y[r]) for i in G.nodes for r in Col_dic.keys() if i in Col_dic[r].nodes_in_path)
    
    linear = IMP.addConstrs((tp[i, j]-tn[i, j] +
        quicksum(Qr[i, r]*G.nodes[j]['demand'] for r in Col_dic.keys() if i in Col_dic[r].nodes_in_path)
        - quicksum(Qr[j, r]*G.nodes[i]['demand'] for r in Col_dic.keys() if j in Col_dic[r].nodes_in_path)
                ==0 for i in Gc.nodes for j in Gc.nodes), name="linear")
    
    TotalTime = IMP.addConstr(quicksum(y[r]*Col_dic[r].travel_time for r in Col_dic.keys()) <= Data.Total_dis_epsilon, name="Total_time")
    visit = IMP.addConstrs((quicksum(Col_dic[r].is_visit(i) * y[r] for r in Col_dic.keys()) == 1 for i in Gc.nodes), name="visit")
    vehicle = IMP.addConstr(quicksum(y[r] for r in Col_dic.keys()) <= M, name="vehicle")
    Inv = IMP.addConstr(quicksum(q[i] for i in Gc.nodes) <= G.nodes[0]['supply'], name="Inv")
    IMP.addConstrs(quicksum(Qr[i, r] for i in Gc.nodes if Col_dic[r].is_visit(i)) <= Q for r in Col_dic.keys())
    IMP.addConstrs(q[i] <= G.nodes[i]['demand'] for i in Gc.nodes)

    IMP.Params.LogToConsole = 0
    IMP.params.TimeLimit = 1500
    IMP.Params.Cutoff = CutOff
    IMP.Params.Threads = 1
    IMP.update()
    IMP.optimize()

    if IMP.status == 2 or IMP.status == 9:
        try:
            yv = IMP.getAttr('x', y)
            qv = IMP.getAttr('x', q)
            Qr = IMP.getAttr('x', Qr)
        
            routes = [Col_dic[e] for e, value in yv.items() if value > 0.5]
            RDP = {}
            for j, r in enumerate(routes):
                RDP[j] = [round(qv[i], 10) for i in r.nodes_in_path]

            return IMP.objVal, routes, RDP
            
        except:
            return float("Inf"), [], []
        
    elif IMP.status == 6:
        return float("Inf"), [], []
    else: 
        return float("Inf"), [], []
