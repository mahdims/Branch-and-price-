import pandas as pd
from math import degrees, atan2, sqrt
import numpy as np
import networkx as nx

def calculateDepotAngle(x,y,G):
    depot_x = G.nodes[0]['location'][0]
    depot_y = G.nodes[0]['location'][1]
    angle = degrees(atan2(y - depot_y, x - depot_x))
    bearing = (90 - angle) % 360
    return bearing
    
class Real_Input():
 
    def __init__(self,NN,M,G,dis,loc_data,Q,C,La,Ga):
        self.NN=int(NN)
        self.M=M
        self.Q=Q
        self.C=C
        self.Lambda=La
        self.Gamma=Ga
        self.distances=dis
        demands=np.array([a for a in nx.get_node_attributes(G,'demand').values()] )
        self.total_demand=sum(demands)        
        self.G=G
        self.loc_data=loc_data
        self.Read_assign_locations()
        self.BigM_dis = 1000000 # depend on locations MaxX*MaxY   
        self.shortest_paths =list(nx.all_pairs_shortest_path_length(self.G))
        #Dis=nx.all_pairs_bellman_ford_path_length(self.G  ,  weight='Travel_time')
        #self.distances = dict( [((i,a[0]),a[1]) for i,k in Dis for a in k.items()]  )   
        self.Gc=G.subgraph(range(1,NN))
        self.Gopen=G.subgraph(range(NN))
        self.BigM= sum([G.nodes[i]['demand'] for i in G.nodes()])
        
    def Read_assign_locations(self):
            #### Node locations ####


        self.G.nodes[0]['location']=( self.loc_data[0,0] , self.loc_data[0,1] )
        self.G.nodes[self.NN+1]['location']=( self.loc_data[0,0] , self.loc_data[0,1] )
        self.G.nodes[0]['AngleWithDepot']=0
        self.G.nodes[self.NN+1]['AngleWithDepot']=0
        
        for i in range(1,self.NN):
            self.G.nodes[i]['location']=( self.loc_data[i,0] , self.loc_data[i,1] )
            angle = calculateDepotAngle(self.loc_data[i,0] , self.loc_data[i,1], self.G)
            self.G.nodes[i]['AngleWithDepot']=angle

    def set_initial_deliveries(self):
        
        for n in range(1,self.NN):
              delivery = self.G.nodes[n]['demand']*self.C
              self.G.nodes[n]['delivery'] = np.ceil(delivery)