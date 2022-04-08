from gurobipy import *
import numpy as np
from utils import utils


def MasterModel(Data, Col_dic, R):
    M = Data.M
    G = Data.G
    Gc = Data.Gc
    Lambda = Data.Lambda
    Gamma = Data.Gamma
    TotalD = Data.total_demand
    
    RMP = Model("Master Problem")
    y_inx = [(r, q) for r in Col_dic.keys() for q in Col_dic[r].RDP.keys()]
    y = RMP.addVars(y_inx, lb=0, name="y")
    RMP._varY = y
    tp = RMP.addVars(Gc.nodes, Gc.nodes, lb=0, name="tp")
    tn = RMP.addVars(Gc.nodes, Gc.nodes, lb=0, name="tn")
    RMP.update()

    RMP.setObjective(quicksum(Gc.nodes[i]['demand'] - quicksum(Col_dic[r].RDP[q][i]*y[r, q] for r, q in y.keys()) for i in Gc.nodes)
                    + (Lambda/TotalD) * quicksum(tp[i, j]+tn[i, j] for i, j in tp.keys())
                    + (Gamma / R) * (Data.Total_dis_epsilon - quicksum(Col_dic[r].travel_time*y[r, q] for r, q in y.keys())))

    linear = RMP.addConstrs((tp[i, j]-tn[i, j]
                + quicksum(Col_dic[r].RDP[q][i]*y[r, q]*G.nodes[j]['demand'] for r, q in y.keys())
                - quicksum(Col_dic[r].RDP[q][j]*y[r, q]*G.nodes[i]['demand'] for r, q in y.keys()) == 0
                             for i in Gc.nodes for j in Gc.nodes), name="linear")
    
    TotalTime = RMP.addConstr(quicksum(y[r, q]*Col_dic[r].travel_time for r, q in y.keys()) <= Data.Total_dis_epsilon, name="Total_time")
    visit = RMP.addConstrs((quicksum((Col_dic[r].is_visit(i) != -1) * y[r, q] for r, q in y.keys()) == 1 for i in Gc.nodes), name="visit")
    vehicle = RMP.addConstr(quicksum(y[r, q] for r, q in y.keys()) <= M, name="vehicle")
    Inv = RMP.addConstr(quicksum(y[r, q]*sum(Col_dic[r].RDP[q]) for r, q in y.keys()) <= G.nodes[0]['supply'], name="Inv")

    # if edge2keep["E"]:
    #    edges = RMP.addConstrs((quicksum(y[r, q] * utils.edge_in_route(edge, Col_dic[r]) for r, q in y.keys()) == 1
    #                            for edge in edge2keep["E"]), name="edge2keep")
    
    RMP.write("Master0.lp")
    RMP.Params.OutputFlag = 0
    RMP.update()
    return RMP
