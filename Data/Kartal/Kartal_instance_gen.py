'''
This file will read an prepare the kartal data set.
first we need to select 20 randomly selected scenarios.

We need the following from the data:
  - distance between nodes
  - population accomodated (assigned) in each node
  - The depot node


The information we need to generates:
  - vehicle number
  - vehicle capacity
  - maximum tour lenght 450 km
  - supply in the depot 0.7 of the demand
'''

import csv
import numpy as np 
import networkx as nx 
import itertools as it
import pandas as pd
from Real_Input import Real_Input
import pickle as Pick

filenames = []
Ssizes = [50, 100, 200, 500, 1000, 20003]
for k in Ssizes:
    filenames.append(('Istanbul', 20, 25, k))


def getdata(fname):
    N = fname[1]
    M = fname[2]
    NS = fname[3]
    percentage = 0.95
    LAMBDA = 0.5 # 0.35, 0.6 or 0.7
    firstData = []
    ref = '_%d_%d_%d.csv' %(N,M,NS)
    with open(''.join(["./", fname[0], ref]), "r") as readfile:
        read = csv.reader(readfile,  delimiter=',')
        for row in read:
            firstData.append(row)

    NS = 2000

    Dis = np.array([np.array(x).astype(float) for i,x in enumerate(firstData[0:N])])
    #B=np.array(firstData[N:N+NS]).astype(np.float)
    B = [list(np.array(x[0:N]).astype(float)) for i,x in enumerate(firstData[N:N+NS])]
    pop = list(np.array(firstData[NS+N][0:N]).astype(float))
    Cost = np.array(firstData[NS+N+1][0:M]).astype(float)
    cap = np.array(firstData[NS+N+2][0:M]).astype(float)
    Cec = np.array(firstData[NS+N+3][0:M]).astype(float)
    p = np.array(firstData[NS+N+4][0:NS]).astype(float)
    budget = (float(7)/7)*np.array(firstData[NS+N+5][0]).astype(float)
    M = len(cap)
    #Dis=np.reshape(Dis,(N,M,NS),'F')    
    
    
    Data={
        'M':M,
        'N':N,
        'NS':NS,
        'budget':budget,
        'percentage':percentage,
        'pop':pop,
        'cap':cap,
        'cec':Cec,
        'cost':Cost,
        #'distance':Dis,
        'demand':B,
        'p':p,
        'lambda':LAMBDA,
        }
    
    return Data


def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)


df = pd.read_excel(r'./fulldis.xls')
disfile = [16, 23, 25, 27, 28, 29, 30, 34, 39, 40, 42, 43, 45]
dis = {}
for i, j in it.combinations(disfile, 2):
    inx = np.where(df.values[:, 1] == i)[0]
    temp = df.values[inx, :]
    inx2 = np.where(temp[:, 2] == j)[0]
    ii = disfile.index(i)
    jj = disfile.index(j)
    dis[ii, jj] = int(temp[inx2, 3][0])
    dis[jj, ii] = dis[ii, jj]


Supply_per = 0.7
M = 3 # number of vehicles
Q = 100 # capaity of the vehicles
La = 0.5
Ga = 0.1

fname = filenames[5:6][0]
Data = getdata(fname)
y = np.loadtxt('./y_20003_0.5.txt')
# dis=Data["distance"]
D = np.array(Data["demand"])
shelters = np.where(sum(y)>0)[0]
shelters = sorted(shelters)
NN = len(shelters) + 1

instance_no = range(13, 14) # [7]
QQ = "A"
scenarios = np.random.randint(2000, size=len(instance_no))

for sinx, s in zip(instance_no, scenarios):
    G = nx.Graph()
    G.add_nodes_from(range(13))
    # add nodes to the graph and import the demands
    for i, shel in enumerate(shelters):
        assigned_DP = np.where(y[:, shel] > 0)[0]
        G.nodes[i+1]['demand'] = sum(D[s, assigned_DP]) + 1
        G.nodes[i+1]['ID'] = shel

    G.nodes[10]['demand'] = 5 * G.nodes[10]['demand']

    # add edges to graph and update the distances
    for i, j in dis.keys():
        G.add_edge(i, j, Travel_distance=dis[i, j])
    # depot dummy node
    G.add_node(NN+1)
    for i in range(1, NN):
        G.add_edge(i, NN+1, Travel_distance=dis[0, i])
    
    demands = np.array([a for a in nx.get_node_attributes(G, 'demand').values()])
    G.nodes[0]['supply'] = sum(np.ceil(demands*Supply_per))
    G.nodes[0]['demand'] = 0
    G.nodes[NN+1]['demand'] = 0

    # location
    df = pd.read_excel(r'./Kartal_CP_Depot.xlsx', engine='openpyxl')
    loc_data = df.values[:, 5:7]
    RealData = Real_Input(NN, M, G, dis, loc_data, Q, Supply_per, La, Ga)
    save_object(RealData, 'Kartal_%s_%d' %(QQ, sinx - 10))
