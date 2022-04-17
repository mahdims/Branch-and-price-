from gurobipy import Model, GRB, quicksum

def Solve_IMP(Data, R, CutOff, Col_dic):
    
    M = Data.M
    Q = Data.Q
    Lambda=Data.Lambda
    Gamma = Data.Gamma
    TotalD = Data.total_demand
    
    IMP = Model("Int_Master")

    y_inx = [(r, q) for r in Col_dic.keys() for q in Col_dic[r].RDP.keys()]
    y = IMP.addVars(y_inx, vtype=GRB.BINARY, name="y")
    tp = IMP.addVars(Data.Gc.nodes, Data.Gc.nodes, lb=0, name="tp")
    tn = IMP.addVars(Data.Gc.nodes, Data.Gc.nodes, lb=0, name="tn")
    IMP.update()

    IMP.setObjective(quicksum(Data.Gc.nodes[i]['demand'] - quicksum(Col_dic[r].RDP[q][i] * y[r, q] for r, q in y.keys()) for i in Data.Gc.nodes)
                     + (Lambda / TotalD) * quicksum(tp[i, j] + tn[i, j] for i, j in tp.keys())
                     + (Gamma / R) * (Data.Total_dis_epsilon - quicksum(Col_dic[r].travel_time * y[r, q] for r, q in y.keys())))

    linear = IMP.addConstrs((tp[i, j] - tn[i, j]
                             + quicksum(Col_dic[r].RDP[q][i] * y[r, q] * Data.G.nodes[j]['demand'] for r, q in y.keys())
                             - quicksum(Col_dic[r].RDP[q][j] * y[r, q] * Data.G.nodes[i]['demand'] for r, q in y.keys()) == 0
                             for i in Data.Gc.nodes for j in Data.Gc.nodes), name="linear")

    TotalTime = IMP.addConstr(quicksum(y[r, q] * Col_dic[r].travel_time for r, q in y.keys()) <= Data.Total_dis_epsilon,
                              name="Total_time")
    visit = IMP.addConstrs(
        (quicksum((Col_dic[r].is_visit(i) != -1) * y[r, q] for r, q in y.keys()) == 1 for i in Data.Gc.nodes), name="visit")
    vehicle = IMP.addConstr(quicksum(y[r, q] for r, q in y.keys()) <= M, name="vehicle")
    Inv = IMP.addConstr(quicksum(y[r, q] * sum(Col_dic[r].RDP[q]) for r, q in y.keys()) <= Data.G.nodes[0]['supply'],
                        name="Inv")

    IMP.Params.OutputFlag = 0
    # IMP.write("MasterInt.lp")
    IMP.params.TimeLimit = 150
    IMP.Params.Cutoff = CutOff
    IMP.update()
    IMP.optimize()

    if IMP.status == 2 or IMP.status == 9:
        try:
            yv = IMP.getAttr('x', y)
            selected_RD = [e for e, value in yv.items() if value > 0.5]
            return IMP.objVal, selected_RD
        except:
            return float("Inf"), []
    else: 
        return float("Inf"), []
    