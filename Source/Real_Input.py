"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""

import pandas as pd
from math import degrees, atan2, sqrt
import numpy as np
import networkx as nx


def calculateDepotAngle(x, y, G):
    depot_x = G.node[0]['location'][0]
    depot_y = G.node[0]['location'][1]
    angle = degrees(atan2(y - depot_y, x - depot_x))
    bearing = (90 - angle) % 360
    return bearing


class Real_Input:

    def __init__(self, NN, M, G, dis, Q, C, La, Ga):
                
        self.NN = int(NN)
        self.M = M
        self.Q = Q
        self.C = C
        self.Lambda = La
        self.Gamma = Ga
        self.distances = dis
        demands = np.array(nx.get_node_attributes(G,'demand').values() )
        self.total_demand = sum(demands)
        self.All_seq = []
        self.G = G
        
        self.Read_assign_locations()
        self.BigM_dis = 1000000 # depend on locations MaxX*MaxY   
        
        self.shortest_paths =list(nx.all_pairs_shortest_path_length(self.G))
        #Dis=nx.all_pairs_bellman_ford_path_length(self.G  ,  weight='Travel_time')
        #self.distances = dict( [((i,a[0]),a[1]) for i,k in Dis for a in k.items()]  )   
        self.Gc = G.subgraph(range(1, NN))
        self.Gopen = G.subgraph(range(NN))
        self.BigM = sum([G.node[i]['demand'] for i in G.nodes()])
        
    def Read_assign_locations(self):
            #### Node locations ####
        df = pd.read_excel (r'G:\My Drive\1-PhD thesis\equitable relief routing\Code\Kartal\Kartal_CP_Depot.xlsx') 
        loc_data=df.values
       
               
        self.G.node[0]['location']=( loc_data[0,5] , loc_data[0,6] )
        self.G.node[self.NN+1]['location']=( loc_data[0,5] , loc_data[0,6] )
        self.G.node[0]['AngleWithDepot']=0
        self.G.node[self.NN+1]['AngleWithDepot']=0
        
        for i in range(1,self.NN):
            self.G.node[i]['location']=( loc_data[i,5] , loc_data[i,6] )
            angle = calculateDepotAngle(loc_data[i,5] , loc_data[i,6], self.G)
            self.G.node[i]['AngleWithDepot']=angle
