import networkx as nx
import matplotlib.pyplot as plt
import random
from gurobipy import *
###############################################
NN=10 # number of nodes
Q=100 # vehicles Capacity
M=4 # number of vehicles 

########### generate the graph  ########### 
p=[] # edge probablities
for i in range(NN*(NN-1)/2):
    p.append(random.random())

G=nx.watts_strogatz_graph(NN,4,p)
G.add_node(NN+1)
for n in range (NN):
    G.add_edge(n,NN+1)
## demand genaration ###
for node in G.node():
    if node != 0:
        G.node[node]['demand']=random.randint(30,50)

## Supply 
total_demand=sum(nx.get_node_attributes(G,'demand').values())
G.node[0]['supply']=int(0.75*total_demand)
G.node[0]['demand']=0
## Travel time generation 
for i,j in G.edges():
    G.edges[i,j]['Travel_time']=random.randint(1,9)

# Convert it to a Digraph
G=nx.DiGraph(G)
################ MODEL 1 ####################

VF_MIP=Model("Vehicle_Flow ")

x=VF_MIP.addVars(G.edges(),M,name="x",vtype=GRB.BINARY)
delta=VF_MIP.addVars(x,name="delta")
u=VF_MIP.addVars(NN,name="u")
v=VF_MIP.addVars(NN,name="v")
z=VF_MIP.addVar(obj=1,name="z")   
VF_MIP.update()

VF_MIP.addConstrs(quicksum(x.select(i,'*','*') )==1 for i in range(1,NN))
VF_MIP.addConstrs(quicksum(x[i,j,k] for j in G.successors(i))== quicksum(x[i,j,k] for j in G.predecessors(i) ) for i in range(1,NN) for k in range(M) )
VF_MIP.addConstrs(quicksum(x[0,j,k] for j in G.successors(0))==1 for k in range(M) )
VF_MIP.addConstrs(quicksum(x[i,NN+1,k] for i in G.predecessors(NN+1))==1  for k in range(M) )
VF_MIP.addConstrs(v[i]<=G.node[i]['demand'] for i in range(1,NN) )
VF_MIP.addConstr(quicksum(v)<=G.node[0]['supply'])
VF_MIP.addConstrs(quicksum(delta[i,j,k] for i,j in G.edges()) <= Q for k in range(M))
VF_MIP.addConstrs(delta[i,j,k]<=v[j] for i,j,k in x.iterkeys() if j<=NN if i<=NN)
VF_MIP.addConstrs(delta[i,j,k]<=G.node[j]['demand']*x[i,j,k] for i,j,k in x.iterkeys() if j<=NN if i<=NN)
VF_MIP.addConstrs(delta[i,j,k]>=v[j]-G.node[j]['demand']*(1-x[i,j,k]) for i,j,k in x.iterkeys() if j<=NN if i<=NN)




VF_MIP.addConstrs(quicksum(G.edges[i,j]['Travel_time']*x[i,j,k] for i,j in G.edges() ) <= z for k in range(M))


VF_MIP.update()
VF_MIP.optimize()

if VF_MIP.status==2:
    print(VF_MIP.objVal)
    Xv=VF_MIP.getAttr('x',x)
        







