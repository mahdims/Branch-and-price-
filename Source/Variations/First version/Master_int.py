# -*- coding: utf-8 -*-
"""
Created on Fri May 10 22:53:26 2019

@author: User
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 16:35:58 2019

@author: User
"""
from gurobipy import *
import numpy as np
from TSP_model import TSP_model
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
    
def Master_int(Data,R,CutOff,Col_dic):
    
    M=Data.M 
    Q=Data.Q  
    G=Data.G
    Gc=Data.Gc
    Lambda=Data.Lambda
    Gamma=Data.Gamma
    TotalD=Data.total_demand    
    
    IMP=Model("Int Master")
        
    y=IMP.addVars(Col_dic.keys(),name="y",vtype=GRB.BINARY)
    tp=IMP.addVars(Gc.nodes,Gc.nodes,lb=0,name="tp")   
    tn=IMP.addVars(Gc.nodes,Gc.nodes,lb=0,name="tn") 
    q=IMP.addVars(G.nodes, name="q")
    inx=[]
    for k in Col_dic.keys():
        for i in Col_dic[k].route:
            inx.append((i,k))
            
    Qr=IMP.addVars(inx, name="q")
    
    IMP.update()
    
    IMP.setObjective( quicksum( Gc.node[i]['demand'] -  q[i] for i in Gc.nodes)
                    + (Lambda/TotalD) * quicksum( tp[i,j]+tn[i,j] for i,j in tp.keys())  
                    + Gamma * (Data.Total_dis_epsilon-quicksum(Col_dic[r].travel_time*y[r] for r in Col_dic.keys() ) )/R  )  
    
    IMP.addConstrs(Qr[i,r] <= q[i] for i in G.node for r in Col_dic.keys() if i in Col_dic[r].route)
    IMP.addConstrs(Qr[i,r] <= G.node[i]['demand']*y[r] for i in G.node for r in Col_dic.keys() if i in Col_dic[r].route)
    IMP.addConstrs(Qr[i,r] >= q[i]-G.node[i]['demand']*(1-y[r]) for i in G.node for r in Col_dic.keys() if i in Col_dic[r].route)
    
    linear = IMP.addConstrs((tp[i,j]-tn[i,j]+
        quicksum(Qr[i,r]*G.node[j]['demand'] for r in Col_dic.keys() if i in Col_dic[r].route  )  
        - quicksum(Qr[j,r]*G.node[i]['demand'] for r in Col_dic.keys() if j in Col_dic[r].route )
                ==0 for i in  Gc.nodes for j in  Gc.nodes) , name="linear")
    
    TotalTime=IMP.addConstr( quicksum( y[r]*Col_dic[r].travel_time for r in Col_dic.keys() ) <= Data.Total_dis_epsilon, name="Total_time" )
    visit = IMP.addConstrs((quicksum((i in Col_dic[r].route )*y[r] for r in Col_dic.keys() )==1 for i in Gc.nodes ), name="visit" )
    vehicle = IMP.addConstr(quicksum(y[r] for r in Col_dic.keys() ) <=  M, name="vehicle") 
    Inv = IMP.addConstr(quicksum(q[i] for i in  Gc.nodes ) <= G.node[0]['supply'], name="Inv" )
    IMP.addConstrs(quicksum(Qr[i,r] for i in  Gc.nodes if i in Col_dic[r].route )<=Q for r in Col_dic.keys())
    IMP.addConstrs( q[i]<=G.node[i]['demand'] for i in  Gc.nodes )
    
    #IMP.write("MasterInt.lp")
    IMP.Params.LogToConsole=0
    IMP.params.TimeLimit=1500
    #IMP.Params.LogFile="Int_Master"
    IMP.Params.Cutoff=CutOff
    IMP.Params.Threads=1
    IMP.update()
    #print(IMP.numVars)
    #print(IMP.NumConstrs)
    IMP.optimize()
    #print ("Number of Columns = %s" %len(Col_dic))

    if IMP.status==2 or IMP.status==9:
        try:
            yv=IMP.getAttr('x',y)
            qv=IMP.getAttr('x',q)
            Qr=IMP.getAttr('x',Qr)
        
            routes=[Col_dic[e] for e,value in yv.items() if value > 0.5]
            RDP={}
            for j,r in enumerate(routes):
                RDP[j]=[round(qv[i],2) for i in r.route]
                #print(r)
                #print(RDP)
            
            
            for r in routes:
                NewRoute=TSP_model(Data.NN,Data.distances,[],[] , r.route[:-1])
                r.route=NewRoute
            return (IMP.objVal,routes,RDP)
            
        except:
            return(float("Inf"),[],[])
        
    elif IMP.status==6:
        return(float("Inf"),[],[])
    else: 
        return(float("Inf"),[],[])    
    