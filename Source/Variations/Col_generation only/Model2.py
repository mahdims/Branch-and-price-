# -*- coding: utf-8 -*-
"""
Created on Thu Sep 20 01:14:24 2018

@author: mahdi
"""
from gurobipy import *
import networkx as nx
def routes_finder(X,NN):
    routes=[]
    starters=[tub[1] for tub in X if tub[0]==0]
    for st in starters:
        X.remove((0,st))
        current_node=st
        route=[0,st]
        while current_node!=NN+1:
            tub = [tub for tub in X if current_node in tub][0]
            X.remove( tub )
            next_node=list(set(tub)-set([current_node]))
            route +=next_node
            if len(next_node)==0:
                ty=0
            current_node = next_node[0]
        routes.append(route)
    return routes
    
def Model2(Data,epsilon):
    NN=Data.NN
    M=Data.M 
    Q=Data.Q  
    G=Data.G
    Gc=Data.Gc
    Gopen=Data.Gopen  
    Lambda=Data.Lambda
    complement=[(j,i) for i,j in G.edges() if i!=0 and j!=NN+1] + [(i,j) for i,j in G.edges()]
    
    
    Travel_time=list(nx.get_edge_attributes(Gopen,'Travel_time').values() )
    BigM=sum(Travel_time)
    print(BigM)
    ################ MODEL 2 ####################
    
    CF_MIP=Model("Two_Commodity_Flow ")
    
    x=CF_MIP.addVars(complement,lb=0,ub=1,name="x",vtype=GRB.BINARY)
    y=CF_MIP.addVars(complement,name="y")
    w=CF_MIP.addVars(complement,name="w")
    u=CF_MIP.addVars(G.nodes,name="u")
    v=CF_MIP.addVars(range(NN),name="v")
    tp=CF_MIP.addVars(Gc.nodes,Gc.nodes,lb=0 , name="tp")   
    tn=CF_MIP.addVars(Gc.nodes,Gc.nodes,lb=0 , name="tn") 
    
    #s=CF_MIP.addVars(Gc.nodes,lb=0,obj=1,name="s")
    
    CF_MIP.update()
    CF_MIP.setObjective(quicksum(G.node[i]['demand'] -v[i] for i in  Gc.nodes)/NN 
                        + (Lambda/(NN*NN)) * quicksum(tp[i,j] + tn[i,j] for i,j in tp.keys()) )
    linear=CF_MIP.addConstrs(tp[i,j]-tn[i,j]+ v[i] - v[j] ==
        G.node[i]['demand']-G.node[j]['demand'] for i in  Gc.nodes for j in  Gc.nodes )
    
    CF_MIP.addConstrs(quicksum(w[i,j]-y[i,j] for j in G.neighbors(i) if j!=0)+quicksum(w[j,i]-y[j,i] for j in G.neighbors(i) if j!=NN+1) == 2*v[i] for i in Gc.node )
    #CF_MIP.addConstrs(quicksum(w[i,j]-y[i,j] for j in G.neighbors(i) ) == 2*v[i] for i in Gc.node )
    CF_MIP.addConstr(quicksum(y.select(0,'*'))==G.node[0]['supply']  )
    CF_MIP.addConstr(quicksum(w.select(0,'*'))==M*Q-G.node[0]['supply']  )
    CF_MIP.addConstr(quicksum(w.select('*',NN+1))==M*Q )
    CF_MIP.addConstrs(y[i,j]+w[i,j]==Q*x[i,j] for i,j in complement)
    CF_MIP.addConstrs(u[j]>=u[i]+G.edges[i,j]['Travel_time']+BigM*(x[i,j]-1) for i,j in complement)
    CF_MIP.addConstrs(u[i]<=epsilon for i in Gc.nodes )
    CF_MIP.addConstrs(v[i]<=G.node[i]['demand'] for i in Gc.nodes )
    #CF_MIP.addConstrs(v[i]+s[i]==G.node[i]['demand'] for i in Gc.nodes )
    CF_MIP.addConstr(quicksum(v) == G.node[0]['supply'] )
    CF_MIP.addConstrs(quicksum(x[i,k] for i in G.neighbors(k) if i != NN+1) == quicksum(x[k,i] for i in G.neighbors(k) if i !=0 ) for k in Gc.node)
    CF_MIP.addConstrs(quicksum(x.select(i,'*') )==1    for i in Gc.node)
    #CF_MIP.addConstrs(quicksum(x[ tuple(sorted([i,k])) ] for i in G.neighbors(k) ) ==2 for k in Gc.node)

    
    
    CF_MIP.update()
    #CF_MIP.Params.OutputFlag=0 
    CF_MIP.optimize()
    CF_MIP.write("model.lp")
    
    Objval=-1000000
    if CF_MIP.status==2:
        Xv=CF_MIP.getAttr('x',x)
        Yv=CF_MIP.getAttr('x',y)
        Wv=CF_MIP.getAttr('x',w)
        Vv=CF_MIP.getAttr('x',v)
        #print([G.node[i]['demand']-Vv[i] for i in range(1,NN)])
        Uv=CF_MIP.getAttr('x',u)
        print(Vv.values())
        #tnv=CF_MIP.getAttr('x',tn)
        #tpv=CF_MIP.getAttr('x',tp)
        Tours=[b[0] for b in Xv.items() if b[1]==1]
        Tours=routes_finder(Tours,NN)
        print(Tours)
        Objval=CF_MIP.objVal
    
    
    return Objval