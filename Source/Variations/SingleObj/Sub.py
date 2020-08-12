"""
Created on Sat Mar 23 16:36:12 2019

@author: Mahdi
"""
from gurobipy import *
import numpy as np
import sys
from itertools import *

def SubProblem(Data):
    NN=Data.NN
    Q=Data.Q  
    G=Data.G
    Gc=Data.Gc
    dis=Data.distances    
       
    # all edges possible now (except xi0 and x8i )
    complement= [i for i in permutations(Gc.nodes,2)] + [(0,i) for i in Gc.nodes] +[(i,NN+1) for i in Gc.nodes]
    
        
    Sub=Model("Sub Problem")
    x=Sub.addVars(complement , name="x" , vtype=GRB.BINARY)
    a=Sub.addVars(G.nodes , name="a"    , vtype=GRB.BINARY)
    q=Sub.addVars(Gc.nodes, name="q")
    Sub.update()
    
    Sub._varX = x    
    Sub._varA = a

    
    Sub.addConstr( quicksum(x[i,j]*dis[(i,j)] for (i,j) in complement if j!=NN+1) <= Data.Maxtour )
    
    Sub.addConstr( quicksum(x.select(0,"*")) == 1) 
    Sub.addConstr( quicksum(x.select("*",NN+1)) == 1) 
    Sub.addConstrs(quicksum(x.select("*",i) ) == quicksum( x.select(i,"*") ) for i in Gc.nodes)
    Sub.addConstrs(quicksum(x.select(i,"*") ) == a[i] for i in G.nodes )
    Sub.addConstrs(q[i] <= G.node[i]['demand']*a[i] for i in Gc.nodes )
    Sub.addConstr( quicksum(q) <= Q )
    Sub.Params.OutputFlag=0     
    Sub.params.LazyConstraints = 1
    return (Sub,x,q,a)