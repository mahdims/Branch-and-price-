import json
import itertools as it
import networkx as nx
from random import random, randint
import numpy as np 
from math import degrees, atan2, sqrt

def calculateDepotAngle(x,y,G):
    depot_x = G.node[0]['location'][0]
    depot_y = G.node[0]['location'][1]
    angle = degrees(atan2(y - depot_y, x - depot_x))
    bearing = (90 - angle) % 360
    return bearing
    
def get_distance(cus1, cus2):
    # Euclideian
    dist = 0 
    dist = sqrt(((cus1[0] - cus2[0]) ** 2) + ((cus1[1] - cus2[1]) ** 2))
    return dist
    
class Input():
    
    def __init__(self,NN,M,Q,C,La,Ga):
                
        self.NN=int(NN)
        self.M=M
        self.Q=Q
        self.C=C
        self.Lambda=La
        self.Gamma=Ga
        p=[] # edge probablities
        for i in range(NN*(NN-1)/2):
            p.append(0.1+random())
        
        G=nx.watts_strogatz_graph(NN,NN/2,p)
        for i in range(1,NN):
            G.add_edge(0,i)
        
        ### adding n+1 node as depot ###
        G.add_node(NN+1)
        for i in range(1,NN):
            if (0,i) in G.edges:
                G.add_edge(i,NN+1)  
        
        ## demand genaration #####
        for node in G.nodes():
            if node != 0 and node!=NN+1:
                G.node[node]['demand']=randint(30,50)
        
        ## Supply 
        demands=np.array(nx.get_node_attributes(G,'demand').values() )
        self.total_demand=sum(demands)
        
        G.node[0]['supply']=sum(np.ceil(demands*self.C))
        G.node[0]['demand']=0
        G.node[NN+1]['demand']=0
        
        self.G=G
        
        
        
        self.Read_assign_locations()
        self.Calculate_travel_distances()
        
        self.Gc=G.subgraph(range(1,NN))
        self.Gopen=G.subgraph(range(NN))
        self.BigM= sum([G.node[i]['demand'] for i in G.nodes()])
    def Read_assign_locations(self):
            #### Node locations ####
        with open("data124.json","r") as inputFile:
            data = json.load(inputFile)
        
               
        self.G.node[0]['location']=( data["depot"]["x"] , data["depot"]["y"] )
        self.G.node[self.NN+1]['location']=( data["depot"]["x"] , data["depot"]["y"] )
        self.G.node[0]['AngleWithDepot']=0
        self.G.node[self.NN+1]['AngleWithDepot']=0
        
        for i in range(1,self.NN):
            self.G.node[i]['location']=(data["nodes"][i]["x"],data["nodes"][i]["y"])
            angle = calculateDepotAngle(data["nodes"][i]["x"], data["nodes"][i]["y"], self.G)
            self.G.node[i]['AngleWithDepot']=angle

        
        ## Travel time generation #####
    def Calculate_travel_distances(self):
        self.distances={}
            
        self.BigM_dis = 1000000 # depend on locations MaxX*MaxY   
       
        
        self.shortest_paths =list(nx.all_pairs_shortest_path_length(self.G))
        
        for i,j in it.permutations(self.G.nodes,2):
            if(i,j) in self.G.edges or (j,i) in self.G.edges:
                pos1=self.G.node[i]['location']
                pos2=self.G.node[j]['location']
                dis=get_distance(pos1, pos2)
                self.G.edges[min([i,j]),max([i,j])]['Travel_time']=dis


        
        Dis=nx.all_pairs_bellman_ford_path_length(self.G  ,  weight='Travel_time')
        self.distances = dict( [((i,a[0]),a[1]) for i,k in Dis for a in k.items()]  )
                
                

    def set_initial_deliveries(self):
        for n in range(1,self.NN):
              delivery = self.G.nodes[n]['demand']*self.C
              self.G.nodes[n]['delivery'] = np.ceil(delivery) 

    
    
    