# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 18:35:47 2019

@author: User
"""
from feasibleSol import Solution
global length
length = Data.distances

class Route():
    edges2keep=None
    routes_set=[]
    Data=[]
    def __init__(self,route,Data):
        Route.Data=Data
        
        self.route=route
        self.RDP=[]
        self.travel_time=None
        self.total_deliveries=None
        
        Travelcost=0
        PreNode=0
        for n_inx,n in enumerate(self.route[1:]): # travel time calculation
            if n==Data.NN+1:
                break
            Travelcost +=  length[PreNode,n]
            
            if Route.edges2keep:
                if any([n in ed for ed in Route.edges2keep]):
                    if (PreNode,n) not in Route.edges2keep and (n,self.route[n_inx+2]) not in Route.edges2keep:
                        Travelcost +=  Data.BigM_dis
                    
            PreNode=n
        self.travel_time=Travelcost
        
    
        #routes_set.append(self)
        
    def set_RDP(self,RDP=None):
        if RDP is None:
            deliveries=np.array(nx.get_node_attributes(Route.Data.G,'demand').values())*Route.Data.C
            deliveries=np.floor(deliveries)
            RDP=[0]*Route.Data.NN            
            for n in self.route[0:-1]: # not include NN+1 in RDPs
                RDP[n]=deliveries[n]
            self.RDP=RDP
        else:
            self.RDP=RDP
        self.total_deliveries=sum(self.RDP) 

    def Feasiblity(self,Data,epsilon):
        epsilon=250
        
        self.time_feasibility = max(0,self.travel_time-epsilon)
        self.time_F= self.time_feasibility==0
        self.cap_feasibility = max(0, self.total_deliveries-Route.Data.Q)
        self.cap_F= self.cap_feasibility ==0
    
    def remove(self,v):
        self.route.remove(v)
        
    def __getitem__(self,index):
        return self.route[index]
        

a=Route([0,2,3,4,8],Data)
a.set_RDP()
b=Route([0,1,6,5,8],Data)
b.set_RDP()
c=Route([0],Data)
c.set_RDP()
Sol = Solution([a,b,c])
Sol.score_cal(1000,1000)
print(epsilon)
for r in Sol.routes:
    print(r.travel_time)
print( Sol.time_feasible )

