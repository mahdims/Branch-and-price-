# this file will read an prepare the kartal data set. 
# first we need to select 20 randomly selected scenarios. 

# We need the following from the data:
##- distance between nodes 
##- population accomodated (assigned) in each node 
##- The depot node 


#The information we need to generates:
# - vehicle number 
# - vehicle capacity
# - maximum tour lenght 450 km
# - supply in the depot 0.7 of the demand  


import csv
import numpy as np 
import networkx as nx 
import itertools as it
import pandas as pd
from Real_Input import Real_Input
import cPickle as Pick

filenames=[]
Ssizes=[50,100,200,500,1000,20003]
for k in Ssizes:
    filenames.append(('Istanbul',20,25,k))

def getdata(fname):
    N=fname[1]
    M=fname[2]
    NS=fname[3]
 
    percentage = 0.95
    LAMBDA = 0.5 # 0.35, 0.6 or 0.7
    firstData=[]
    ref='_%d_%d_%d.csv' %(N,M,NS)
    ifile  = open(''.join(["G:\My Drive\\1-PhD thesis\my codes\data\\" ,fname[0],ref]) , "rb")
    #ifile  = open(dir_path+'\data\dataoutP2_%d_%d_%d.csv' %(N,M,NS), "rb")
    read=csv.reader(ifile)
    for row in read: firstData.append(row)
    ifile.close()
    
    NS=2000

    Dis=np.array([np.array(x).astype(np.float) for i,x in enumerate(firstData[0:N])])
    #B=np.array(firstData[N:N+NS]).astype(np.float)
    B=[list(np.array(x[0:N]).astype(np.float)) for i,x in enumerate(firstData[N:N+NS])]
    pop=list(np.array(firstData[NS+N][0:N]).astype(np.float))
    Cost=np.array(firstData[NS+N+1][0:M]).astype(np.float)
    cap=np.array(firstData[NS+N+2][0:M]).astype(np.float)
    Cec=np.array(firstData[NS+N+3][0:M]).astype(np.float)
    p=np.array(firstData[NS+N+4][0:NS]).astype(np.float)
    budget=(float(7)/7)*np.array(firstData[NS+N+5][0]).astype(np.float)     
    M=len(cap)    
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




df = pd.read_excel (r'G:\My Drive\1-PhD thesis\equitable relief routing\Code\Kartal\fulldis.xls') #(use "r" before the path string to address special character, such as '\'). Don't forget to put the file name at the end of the path + '.xlsx'
disfile   = [16,23,25,27,28,29,30,34,39,40,42,43,45]
dis={}
for i,j in it.combinations(disfile,2):
    inx=np.where( df.values[:,1] == i )[0]
    temp=df.values[inx,:]
    inx2= np.where(temp[:,2]==j )[0]
    ii=disfile.index(i)
    jj=disfile.index(j)
    dis[ii,jj]=temp[inx2,3][0]
    dis[jj,ii]=dis[ii,jj]



Supply_per=0.7
M =3 # number of vehicles
Q=100 # capaity of the vehicles 
QQ="T"
La=0.5
Ga=0.1

fname=filenames[5:6][0]
Data=getdata(fname)
y=np.loadtxt('G:\My Drive\\1-PhD thesis\my codes\y_20003_0.5.txt')
#dis=Data["distance"]
D=np.array(Data["demand"])
shelters = np.where(sum(y)>0)[0]
shelters=sorted(shelters)
NN=len(shelters) + 1

scenarios = np.random.randint(2000,size=10) # seclec the instances from scenarios

for sinx,s in enumerate(scenarios):
    G=nx.Graph()
    G.add_nodes_from(range(13))
    # add nodes to the graph and import the demands
    for i,shel in enumerate(shelters):  
        assigned_DP=np.where(y[:,shel]>0)[0]
        G.node[i+1]['demand']=sum(D[s,assigned_DP])
        G.node[i+1]['ID']= shel
    
    ## add edges to graph and update the distances 

    for i,j in dis.keys(): 
        G.add_edge(i,j,Travel_distance = (1+1.5*np.random.rand()) * dis[i,j] )
    
    
    ## depot dummy node 
    G.add_node(NN+1)
    for i in range(1,NN):
        G.add_edge(i,NN+1,Travel_distance =dis[0,i])
    
    demands=np.array(nx.get_node_attributes(G,'demand').values() )
    G.node[0]['supply']=sum(np.ceil(demands*Supply_per))
    G.node[0]['demand']=0
    G.node[NN+1]['demand']=0
    
    
    ## location  
    df = pd.read_excel (r'G:\My Drive\1-PhD thesis\equitable relief routing\Code\Kartal\Kartal_CP_Depot.xlsx') 
    loc_data=df.values[:,5:7]
    
    RealData=Real_Input(NN,M,G,dis,loc_data,Q,Supply_per,La,Ga)
    save_object( RealData , 'Kartal_%s_%d' %(QQ,sinx+1) )
    