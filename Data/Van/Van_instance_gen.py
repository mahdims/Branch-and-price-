import xlrd
from os import path
from math import floor
import numpy as np
import pandas as pd
import networkx as nx 
import itertools as it
from Real_Input import Real_Input
import pickle as Pick


def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)


# read the distances
BASEDIR = path.dirname(path.realpath(__file__))
TT_sheet = pd.read_excel(BASEDIR + '/VanRawData.xlsx', sheet_name="travel_times", engine='openpyxl')
depot_dis = list(TT_sheet.iloc[3:, 2].values)

dis1 = []
for i in range(5, 99):
    dis1.append(list(TT_sheet.iloc[3:, i].values))

dis = {}
for i, j in it.permutations(range(95), 2):
    dis[i, j] = dis1[i-1][j-1]
    if i == 0:
        dis[i, j] = depot_dis[j-1]
    if j == 0:
        dis[i, j] = depot_dis[i-1]

# specify the problem parameters
Supply_per = 0.7
La = 0.5
Ga = 0.1

for NN in [94]: #[60,30,15]:
    M = {94: 12,
        60: 9,
         30: 5,
         15: 3}   # number of vehicles
   
    node_sheet = pd.read_excel(BASEDIR + '/VanRawData.xlsx',
                               sheet_name=f"NS{NN}",
                               engine='openpyxl')
    BDemand = np.array(node_sheet.iloc[:, 5])
    WDemand = np.array(node_sheet.iloc[:, 6])
    totalDemand = sum(BDemand)
    # capacity of the vehicle
    Q = floor((totalDemand*Supply_per) / M[NN])
    NodeID = np.array(node_sheet.iloc[:, 1])
    for inst in range(1, 6):
        D = 0.75*BDemand + np.random.rand(NN)*(WDemand-BDemand)
        G = nx.Graph()
        G.add_nodes_from([(i, {"demand": D[i-1]}) for i in range(1, NN)])
        G.add_node(0)
        Instance_dis = {}
        for i, j in it.permutations(G.nodes(), 2):
            if i != 0:
                NodeID_i = NodeID[i-1]
            else:
                NodeID_i = 0
            if j != 0:
                NodeID_j = NodeID[j-1]
            else:
                NodeID_j = 0
            Updated_dis = dis[NodeID_i, NodeID_j]
            G.add_edge(i, j, Travel_distance=Updated_dis)
            Instance_dis[i, j] = Updated_dis

        # depot dummy node
        G.add_node(NN+1)
        for i in range(1, NN):
            G.add_edge(i, NN+1, Travel_distance=dis[0, i])
        
        demands = np.array([a for a in nx.get_node_attributes(G, 'demand').values()])
        G.nodes[0]['supply'] = sum(np.ceil(demands*Supply_per))
        G.nodes[0]['demand'] = 0
        G.nodes[NN+1]['demand'] = 0
        Xcoord = np.array([0]+list(node_sheet.iloc[:, 7].values))
        Ycoord = np.array([0]+list(node_sheet.iloc[:, 8].values))
        loc_data = np.vstack((Xcoord, Ycoord)).transpose()
        RealData = Real_Input(NN, M[NN], G, dis, loc_data, Q, Supply_per, La, Ga)
        save_object(RealData, 'Van_%d_%d_%d' % (NN, M[NN], inst))
