import xlrd
from math import floor
import numpy as np 
import networkx as nx 
import itertools as it
import pandas as pd
from Real_Input import Real_Input
import cPickle as Pick

def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)


## read the distances 

loc = ('G:\My Drive\\1-PhD thesis\equitable relief routing\Code\Van\VanRawData.xlsx') 
wb = xlrd.open_workbook(loc) 

dis1=[]
TT_sheet = wb.sheet_by_name("travel_times")
depot_dis= list( TT_sheet.col_values(2)[4:] )

for i in range(4,98):
    dis1.append(list(TT_sheet.row_values(i)[5:] ))

dis={}
for i,j in it.permutations(range(95),2):
    dis[i,j] = dis1[i-1][j-1]
    if i==0:
        dis[i,j] = depot_dis[j-1]
    if j==0:
        dis[i,j] = depot_dis[i-1]


## specify the problem paremeters
Supply_per=0.7
La=0.5
Ga=0.1


for NN in [60]:#[60,30,15]:
    M ={60: 9,
        30: 5,
        15: 3 }   # number of vehicles
   
    node_sheet=wb.sheet_by_name("NS%s" %NN)
    BDemand=np.array(node_sheet.col_values(5)[1:] )
    WDemand=np.array(node_sheet.col_values(6)[1:] )
    totalDemand=sum(BDemand)
    # capaity of the vehicles
    Q=  floor((totalDemand*Supply_per) / M[NN])
    NodeID = np.array(node_sheet.col_values(1)[1:] )
    for inst in range(9,10):
        D=0.75*BDemand+np.random.rand(NN)*(WDemand-BDemand)
        G=nx.Graph()
        G.add_nodes_from( [(i,{"demand":D[i-1]}) for i in range(1,NN)] )
        G.add_node(0)
        
        Instance_dis={}
        for i,j in it.permutations(G.node,2):
            if i!=0:
                NodeID_i=NodeID[i-1]
            else:
                NodeID_i=0
            if j!=0:
                NodeID_j=NodeID[j-1]
            else:
                NodeID_j=0
            Updated_dis= dis[NodeID_i,NodeID_j]
            G.add_edge(i,j,Travel_distance = Updated_dis  )
            Instance_dis[i,j] = Updated_dis
            
        ## depot dummy node 
        G.add_node(NN+1)
        for i in range(1,NN):
            G.add_edge(i,NN+1,Travel_distance=dis[0,i])
        
        demands=np.array(nx.get_node_attributes(G,'demand').values() )
        G.node[0]['supply']=sum(np.ceil(demands*Supply_per))
        G.node[0]['demand']=0
        G.node[NN+1]['demand']=0
        Xcoord = np.array([0]+node_sheet.col_values(7)[1:] )
        Ycoord = np.array([0]+node_sheet.col_values(8)[1:] )   
        loc_data=np.vstack((Xcoord, Ycoord)).transpose()
        RealData=Real_Input(NN,M[NN],G,dis,loc_data,Q,Supply_per,La,Ga)
        save_object( RealData , 'Van_%d_%d_%d' %(NN,M[NN],inst) )
            
    
    
        