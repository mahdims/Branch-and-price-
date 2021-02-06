import networkx as nx
import itertools as it
import matplotlib.pyplot as plt
import random
from itertools import *
from gurobipy import *
###############################################

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
            current_node = next_node[0]
        routes.append(route)
    return routes
    
def Time_Calc(Dis,NN,R):
    Travelcost=0
    PreNode=0
    for n in R[1:-1]: # travel time calculation
        Travelcost +=  Dis[PreNode,n]
        PreNode=n
    return Travelcost
    
def subtourelim(model, where):
  if where == GRB.callback.MIPSOL:
    selected = {}
    for k in range(M):
        selected[k] = []
        
    sol={}
    # make a list of edges selected in the solution
    for i,j in complement:
        for k in range(M):
            sol[i,j,k] = model.cbGetSolution(model._vars[i,j,k])
            if sol[i,j,k] > 0.5:
                selected[k].append( (i,j) )
    # find the shortest cycle in the selected edge list
    tour = Get_the_Subtours(selected)
    if len(tour):
      # add a subtour elimination constraint
      expr = 0
      for i in range(len(tour)):
        for j in range(i+1, len(tour)):
            for k in range(M):
                expr += model._vars[tour[i], tour[j],k]
                expr += model._vars[tour[j], tour[i],k]
      model.cbLazy(expr <= len(tour)-1)



# Given a list of edges, finds the shortest subtour
def Get_the_Subtours(edges):
    NN=G.number_of_nodes()-1
    Resulting_G=nx.Graph()
    Resulting_G.add_nodes_from(G.nodes())
 
    for edgelist in edges.values():
        for e in edgelist:
            Resulting_G.add_edge( *e  ) 
        #path=nx.shortest_path(G,e[0],e[1],weight ='Travel_time')
        #i=e[0]
        #for j in path[1:]:
        #    Resulting_G.add_edge(   i,j  ,   Travel_time=G.edges[i,j]['Travel_time']  )     
    subtours=[c for c in sorted(nx.connected_components(Resulting_G), key=len, reverse=True)]
    # Put the tour with depot nodes at first
    for s in subtours:
        if 0 in s and NN+1 in s:
            subtours.remove(s)
    if subtours:
        return list(subtours[subtours.index(min( subtours , key=lambda x :len(x) ) ) ] )
    else:
        return []


def Model1(Data,R):

    global Gc,G,NN ,complement ,M
    Gc = Data.Gc
    NN = Data.NN
    M = Data.M
    Q = Data.Q
    G = Data.G
    Gc = Data.Gc
    Lambda = Data.Lambda
    Gamma = Data.Gamma
    
    complement = [i for i in permutations(Gc.nodes, 2)] + [(0, i) for i in Gc.nodes] + [(i, NN+1) for i in Gc.nodes]
    Dis = Data.distances
    ''' 
    Dis={}
    paths = dict(nx.all_pairs_bellman_ford_path(G))
    for i,j in it.combinations(G.node,2):
        path=paths[i][j]
        travel_dis=0
        pernode=path.pop(0)
        while len(path):
            Cnode = path.pop(0)
            travel_dis += G.edges[pernode,Cnode]["Travel_distance"]
            pernode = Cnode
        Dis[i,j] = travel_dis
        Dis[j,i] = travel_dis
    '''
    
    TotalD = Data.total_demand
    
    VF_MIP = Model("Vehicle_Flow ")
    
    x = VF_MIP.addVars(complement, M, name="x", vtype=GRB.BINARY)
    delta = VF_MIP.addVars(x, lb=0, name="delta")
    v = VF_MIP.addVars(Gc.nodes, lb=0, name="v")
    tp = VF_MIP.addVars(Gc.nodes, Gc.nodes, lb=0, name="tp")
    tn = VF_MIP.addVars(Gc.nodes, Gc.nodes, lb=0, name="tn")
    VF_MIP.update()
    
    VF_MIP.setObjective(quicksum(G.nodes[i]['demand'] - v[i] for i in Gc.nodes)
                        + (Lambda/TotalD) * quicksum(tp[i, j] + tn[i, j] for i, j in tp.keys())
                        +Gamma/R * (Data.Total_dis_epsilon - quicksum(Dis[i, j]*x[i, j, k]
                                                                        for k in range(M) for i,j in complement if j!=NN+1 ) ) )
    
    VF_MIP.addConstr(quicksum(Dis[i, j] * x[i, j, k] for k in range(M) for i, j in complement if j != NN+1) <= Data.Total_dis_epsilon)
    VF_MIP.addConstrs(tp[i, j] - tn[i, j] ==
        v[j]*G.nodes[i]['demand']-v[i]*G.nodes[j]['demand'] for i in Gc.nodes for j in Gc.nodes)
   
    VF_MIP.addConstrs(quicksum(x.select(i, '*', '*')) == 1 for i in range(1, NN))
    VF_MIP.addConstrs(quicksum(x.select(i, '*', k)) == quicksum(x.select('*', i, k)) for i in Gc.nodes for k in range(M))
    VF_MIP.addConstrs(quicksum(x.select(0, '*', k)) == 1 for k in range(M))
    VF_MIP.addConstrs(quicksum(x.select('*', NN+1, k)) == 1 for k in range(M))
    VF_MIP.addConstrs(v[i] <= G.nodes[i]['demand'] for i in Gc.nodes)
    VF_MIP.addConstr(quicksum(v) <= G.nodes[0]['supply'])
    VF_MIP.addConstrs(quicksum(Dis[i, j]*x[i, j, k] for i, j in complement if j != NN+1) <= Data.Maxtour for k in range(M))
    VF_MIP.addConstrs(quicksum(delta.select('*', '*', k)) <= Q for k in range(M))
    VF_MIP.addConstrs(delta[i, j, k] <= v[j] for i, j, k in x.iterkeys() if j != NN+1)
    VF_MIP.addConstrs(delta[i, j, k] <= G.nodes[j]['demand'] * x[i, j, k] for i, j, k in x.iterkeys() if j != NN+1)
    VF_MIP.addConstrs(delta[i, j, k] >= v[j]-G.nodes[j]['demand']*(1-x[i, j, k]) for i, j, k in x.iterkeys() if j != NN+1)

    VF_MIP._vars = x
    VF_MIP.update()
    VF_MIP.params.LazyConstraints = 1
    VF_MIP.params.TimeLimit = 7200
    VF_MIP.optimize(subtourelim)
    
    Objval="infeasible"
    if VF_MIP.status == 2:
        Objval = VF_MIP.objVal
        Vv = VF_MIP.getAttr('x', v)
        Xv = VF_MIP.getAttr('x', x)
        Tnv = VF_MIP.getAttr('x', tn)
        Tours = [b[0] for b in Xv.items() if b[1] > 0.5]
        routes = []
        vehicles = {}
        
        for k in range(M):
            vehicles[k] = [(tub[0], tub[1]) for tub in Tours if tub[2] == k]
            one_V = vehicles[k]
            route = routes_finder(one_V, NN)[0]
            RDP = [0]
            for i in route[1:-1]:
                RDP.append(round(Vv[i], 1))
            RDP.append(0)
            routes.append((route, RDP))
        for r in routes:
            print(r[0])
            print(r[1])
            print("Total delivery in this tour: %s" % sum(r[1]))
            print("The Tour length is : %s \n" % round(Time_Calc(Dis, NN, r[0]), 1))

    return VF_MIP.objVal, VF_MIP.ObjBound, VF_MIP.Runtime,  VF_MIP.MIPGap




