# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 16:35:58 2019

@author: User
"""
from gurobipy import *

def MasterModel(Data,Paths):
    
    NN=Data.NN
    M=Data.M 
    Q=Data.Q  
    G=Data.G
    Gc=Data.Gc
    Lambda=Data.Lambda
    RMP=Model("Master Problem")
        
    y=RMP.addVars(len(Paths),lb=0,ub=1,name="y")
    tp=RMP.addVars(Gc.nodes,Gc.nodes,lb=0,name="tp")   
    tn=RMP.addVars(Gc.nodes,Gc.nodes,lb=0,name="tn") 
    RMP.update()
    
    RMP.setObjective( quicksum( Gc.node[i]['demand'] - quicksum(Paths[r].RDP[i]*y[r] for r in range(len(Paths))) for i in Gc.nodes)/NN 
                    + (Lambda/(NN*NN)) * quicksum( tp[i,j]+tn[i,j] for i,j in tp.keys() )    )  
    
    linear = RMP.addConstrs((tp[i,j]-tn[i,j]+
        quicksum(Paths[r].RDP[i]*y[r] for r in range(len(Paths)) if i in Paths[r] )  
        - quicksum(Paths[r].RDP[j]*y[r] for r in range(len(Paths)) if j in Paths[r] )
                ==G.node[i]['demand']-G.node[j]['demand'] for i in  Gc.nodes for j in  Gc.nodes) , name="linear")

    visit = RMP.addConstrs((quicksum((i in Paths[r].route )*y[r] for r in range(len(Paths)) )==1 for i in Gc.nodes ), name="visit" )
    vehicle = RMP.addConstr(quicksum(y[r] for r in range(len(Paths)) ) <=  M, name="vehicle") 
    Inv = RMP.addConstr(quicksum(y[r]*sum(Paths[r].RDP) for r in range(len(Paths)) ) <= G.node[0]['supply'], name="Inv" )
    
    RMP.write("Master.lp")
    RMP.Params.OutputFlag=0 
    RMP.update()
    return ( RMP , y , (tp,tn) )
    
    '''
    RMP.optimize()
    if RMP.status==2:
        print("Master Problem Optimal Value: %d" %RMP.objVal)
        
        
            #Yv=RMP.getAttr('x',y)
            #selectedRoutes=[a[0][0] for a in Yv.items() if a[1]!=0]
            #LongestRoute=max(np.array(Travelcost)[selectedRoutes]
    else:
        sys.exit("##### Master problem infeasible #####")    
    '''   
    
