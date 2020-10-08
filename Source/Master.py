# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 16:35:58 2019

@author: User
"""
from gurobipy import *
import numpy as np

def edge_in_route(edge,route):
    
    i=edge[0]
    j=edge[1]
    # this function will check if route use edge i-j or not
    indicator=0
    if i in route and j in route :
        I_inx=np.where(np.array(route)==i)[0][0]
        if I_inx==0 and route[1]==j: return 1
        if I_inx==len(route)-1 and route[-2]==j: return 1
        if  I_inx!=0 and I_inx!=len(route)-1:
            if route[I_inx+1]==j or route[I_inx-1]==j:
                indicator=1
    return indicator
    
def MasterModel(Data,Col_dic,R,edge2keep=None):
    
    M=Data.M 
    Q=Data.Q  
    G=Data.G
    Gc=Data.Gc
    Lambda=Data.Lambda
    Gamma = Data.Gamma    
    
    TotalD=Data.total_demand    
    
    RMP=Model("Master Problem")
    y_inx = [(r,q) for r in Col_dic.keys() for q in Col_dic[r].RDP.keys()]
    y=RMP.addVars(y_inx ,lb=0,ub=1,name="y")
    tp=RMP.addVars(Gc.nodes,Gc.nodes,lb=0,name="tp")   
    tn=RMP.addVars(Gc.nodes,Gc.nodes,lb=0,name="tn") 
    RMP.update()

    RMP.setObjective( quicksum( Gc.nodes[i]['demand'] - quicksum(Col_dic[r].RDP[q][i]*y[r,q] for r,q in y.keys() ) for i in Gc.nodes)
                    + (Lambda/TotalD) * quicksum( tp[i,j]+tn[i,j] for i,j in tp.keys() )
                    + (Gamma / R ) * ( Data.Total_dis_epsilon - quicksum(Col_dic[r].travel_time*y[r,q] for r,q in y.keys() ) ))

    linear = RMP.addConstrs((tp[i,j]-tn[i,j]+
        quicksum(Col_dic[r].RDP[q][i]*y[r,q]*G.nodes[j]['demand'] for r,q in y.keys()  )
        - quicksum(Col_dic[r].RDP[q][j]*y[r,q]*G.nodes[i]['demand'] for r,q in y.keys() )
                ==0 for i in  Gc.nodes for j in  Gc.nodes) , name="linear")
    
    TotalTime=RMP.addConstr( quicksum( y[r,q]*Col_dic[r].travel_time for r,q in y.keys() ) <= Data.Total_dis_epsilon, name="Total_time" )
    visit = RMP.addConstrs((quicksum((i in Col_dic[r].route )*y[r,q] for r,q in y.keys() )==1 for i in Gc.nodes ), name="visit" )
    vehicle = RMP.addConstr(quicksum(y[r,q] for r,q in y.keys() ) <=  M, name="vehicle")
    Inv = RMP.addConstr(quicksum(y[r,q]*sum(Col_dic[r].RDP[q]) for r,q in y.keys() ) <= G.nodes[0]['supply'], name="Inv" )
    
    if edge2keep:
        edges= RMP.addConstrs(  (quicksum( y[r,q]* edge_in_route(edge,Col_dic[r].route) for r,q in y.keys())==1  for edge in edge2keep) , name="edge2keep")
    
    
    
    #RMP.write("Master0.lp")
    RMP.Params.OutputFlag=0 
    RMP.update()
    return (RMP)
    
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
    
