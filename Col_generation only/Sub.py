# -*- coding: utf-8 -*-
"""
Created on Sat Mar 23 16:36:12 2019

@author: User
"""
from gurobipy import *
import numpy as np

def SubProblem(Data,epsilon,AllDual):
    NN=Data.NN
    Q=Data.Q  
    G=Data.G
    Gc=Data.Gc
    Gopen=Data.Gopen
    linear=np.array(AllDual[0:(NN-1)*(NN-1)]).reshape((NN-1,NN-1)) #get_constraints(RMP, name='linear')
    visit=np.array(AllDual[(NN-1)*(NN-1):(NN-1)*(NN-1)+NN-1])
    vehicle=np.array(AllDual[-2])
    Inv=np.array(AllDual[-1])
    
    complement=[(j,i) for i,j in G.edges() if i!=0 and j!=NN+1] + [(i,j) for i,j in G.edges()]    

    Sub=Model("Sub Problem")
    x=Sub.addVars(complement , name="x" , vtype=GRB.BINARY)
    a=Sub.addVars(G.nodes , name="a"    , vtype=GRB.BINARY)
    q=Sub.addVars(Gc.nodes, name="q")
    Sub.update()
    
    Sub.setObjective(-quicksum((q[i]-q[j])*linear[i-1,j-1] for i in Gc.nodes for j in Gc.nodes)   
                        - quicksum(a[i]*visit[i-1] for i in Gc.nodes)
                        - quicksum(q)*(Inv+1/NN)-vehicle, GRB.MINIMIZE)
    
    
    Sub.addConstr( quicksum(x[i,j]*G.edges[i,j]['Travel_time'] for (i,j) in Gopen.edges) <= epsilon )
    Sub.addConstr( quicksum(x.select(0,"*")) == 1) 
    Sub.addConstr( quicksum(x.select("*",NN+1)) == 1) 
    Sub.addConstrs(quicksum(x.select("*",i) ) == quicksum( x.select(i,"*") ) for i in Gc.nodes)
    Sub.addConstrs(quicksum(x.select(i,"*") ) == a[i] for i in G.nodes )
    Sub.addConstrs(q[i] <= G.node[i]['demand']*a[i] for i in Gc.nodes )
    Sub.addConstr( quicksum(q) <= Q )
    Sub.Params.OutputFlag=0      
    return (Sub,x,q,a)