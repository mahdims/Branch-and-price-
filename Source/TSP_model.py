# -*- coding: utf-8 -*-
"""
Created on Sat Apr 20 13:57:47 2019

@author: User
"""
import networkx as nx 
from  gurobipy import *
from itertools import combinations

# Callback - use lazy constraints to eliminate sub-tours

def subtourelim(model, where):
  if where == GRB.callback.MIPSOL:
    selected = []
    sol={}
    # make a list of edges selected in the solution
    for i in Gnodes:
      for j in Gnodes :
          if j!=i:
              sol[i,j] = model.cbGetSolution(model._vars[i,j])
              if sol[i,j] > 0.5:
                  selected.append( (i,j) )
    # find the shortest cycle in the selected edge list
    tour = subtour(selected)
    if len(tour) < n:
      # add a subtour elimination constraint
      expr = 0
      for i in range(len(tour)):
        for j in range(i+1, len(tour)):
          expr += model._vars[tour[i], tour[j]]
          expr += model._vars[tour[j], tour[i]]
      model.cbLazy(expr <= len(tour)-1)



# Given a list of edges, finds the shortest subtour

def subtour(edges):
  visited = {}
  selected = {}
  for i in Gnodes:
        visited[i] = False
        selected[i] = []
  cycles = []
  lengths = []
  
  for x,y in edges:
    selected[x].append(y)
  while True:
    current = list(visited.keys())[list(visited.values()).index(False)]
    thiscycle = [current]
    while True:
      visited[current] = True
      neighbors = [x for x in selected[current] if not visited[x]]
      if len(neighbors) == 0:
        break
      current = neighbors[0]
      thiscycle.append(current)
    cycles.append(thiscycle)
    lengths.append(len(thiscycle))
    if sum(lengths) == n:
      break
  return cycles[lengths.index(min(lengths))]



def TSP_model(NN,dis,edges2keep,edges2avoid ,Nodes):

    global Gnodes , n
    try:
        Gnodes=Nodes.route
    except:
        Gnodes=Nodes
        
    for i in Gnodes:
        dis[i,0]=0
    n = len(Gnodes)

    TSP = Model("Tsp")
    
    # Create variables
    
    x = {}
    for i,j in combinations(Gnodes,2):
         x[i,j] = TSP.addVar(obj=dis[i, j], vtype=GRB.BINARY, name='e'+str(i)+'_'+str(j))
         x[j,i] = TSP.addVar(obj=dis[j, i], vtype=GRB.BINARY, name='e'+str(j)+'_'+str(i))
       
         #x[i,i].ub = 0
    
    TSP._vars = x
    
    TSP.update()
    
    # Add degree-2 constraint, and forbid loops
    TSP.addConstrs(quicksum(x[i,j] for j in Gnodes if j!=i) == quicksum(x[j,i] for j in Gnodes if j!=i)  for i in Gnodes)
    TSP.addConstr(quicksum(x[0,j] for j in Gnodes if j!=0) ==1)
    TSP.addConstrs( quicksum(x[i,j] for j in Gnodes if j!=i)  == 1 for i in Gnodes )
    
    if edges2keep:
        for i,j in  edges2keep:
            
            if j in Gnodes and i in Gnodes: # if both node exist in Gnodes
                if i==0: 
                    TSP.addConstr(x[0,j]==1)
                else:
                    TSP.addConstr(x[i,j] + x[j,i] >=1 )


    if edges2avoid:
        for i,j in  edges2avoid:
            
            if j in Gnodes and i in Gnodes: # if both node exist in Gnodes
                if i==0: 
                    TSP.addConstr(x[0,j]==0)
                else:
                    TSP.addConstr(x[i,j] + x[j,i] ==0 )

        
    TSP.update()
        
    # Optimize model
    TSP.Params.OutputFlag=0 
    
    TSP.params.LazyConstraints = 1
    TSP.optimize(subtourelim)
    if TSP.status!=2:
        return Gnodes+[NN+1]
    solution = TSP.getAttr('x', x)
    selected = [(i,j) for i,j in x.keys() if solution[i,j] > 0.5]
    route = subtour(selected)
    assert len(route) == n
    
    return route+[NN+1]

