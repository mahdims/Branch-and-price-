import random
import numpy as np
import copy
import sys
import networkx as nx
import matplotlib.pyplot as plt
from math import sqrt
from TSP_model import TSP_model
### Classes
class Solution():
    epsilon=None
    Data=None
    
    
    def __init__(self,routes):
        self.routes=routes
        
    def score_cal(self, alpha,beta):
        violated_time = 0
        violated_cap = 0
        total_time = 0
        for route in self.routes:
            route.Feasiblity( Solution.Data )
            violated_time += route.time_feasibility
            violated_cap  += route.cap_feasibility
            total_time    += route.travel_time
        self.time_feasible = violated_time == 0
        self.cap_feasible = violated_cap == 0
        self.feasible = self.time_feasible and self.cap_feasible
        self.score = total_time + alpha*violated_time + beta*violated_cap
        
        
    def Find_the_route(self,Vs):
        
        for i,r in enumerate(self.routes):
           if all([v in r.route  for v in Vs]):
                    return i

    
    def Replace(self,route_inx,New_route)   :
        self.routes[route_inx]=New_route
    
    def Inseration_cost(self,alpha,beta,nodes,node_route,des_route,length):
        
        NewSol=copy.deepcopy(self)
        for v in nodes :
            NewSol.routes[node_route].route.remove( v )
        NewSol.routes[node_route] = Optimize( Solution.Data , [NewSol.routes[node_route]] ,length)[0]
        
        if des_route < len(NewSol.routes):
            for v in nodes :
                NewSol.routes[des_route].route.insert(-1,v)
            NewSol.routes[des_route]= Optimize( Solution.Data , [NewSol.routes[des_route]] ,length )[0]
        else:
            newpath=TSP_model(Solution.Data.NN,length ,Route.E2K,Route.edges2avoid ,[0]+nodes) # just to find the best sequence of nodes
            newpath = Route( newpath , Solution.Data , length)
            newpath.set_RDP()
            NewSol.routes.append(newpath)
        
        
        if len(NewSol.routes[node_route].route)<=1:
            del NewSol.routes[node_route]
            
        NewSol.score_cal(alpha,beta)
        
        return NewSol
        
            

class Route():
    E2K=None
    edges2keep = None
    edges2avoid=None
    routes_set = []
    Data = []
    Class_RDP=None
    def __init__(self,route,Data,length):
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
                if n in Route.edges2keep.keys():
                    if PreNode != Route.edges2keep[n] and self.route[n_inx+2] != Route.edges2keep[n]:
                        Travelcost +=  Data.BigM_dis
                    
            PreNode=n
        self.travel_time=Travelcost
        
    
        #routes_set.append(self)
        
    def set_RDP(self,RDP=None):
        if RDP is not None:
            self.RDP=RDP
        elif Route.Class_RDP is not None:
            temp_RDP=[0]*Route.Data.NN
            for n in self.route[0:-1]:
                temp_RDP[n]=Route.Class_RDP[n]
            self.RDP=temp_RDP
        else:
            deliveries=np.array(nx.get_node_attributes(Route.Data.G,'demand').values())*Route.Data.C
            deliveries=np.floor(deliveries)
            RDP=[0]*Route.Data.NN            
            CAP=0
            for n in self.route[0:-1]: # not include NN+1 in RDPs
                if deliveries[n]+CAP<=Data.Q:
                    RDP[n]=deliveries[n]
                    CAP+=deliveries[n]
                else:
                    RDP[n]=0
            self.RDP=RDP
        
            
        self.total_deliveries=sum(self.RDP) 

    def Feasiblity(self,Data):
        self.time_feasibility = max(0,self.travel_time-Data.Maxtour)
        self.time_F= self.time_feasibility==0
        self.cap_feasibility = max(0, self.total_deliveries-Data.Q)
        self.cap_F= self.cap_feasibility ==0
    
    def remove(self,v):
        self.route.remove(v)
        
    def __getitem__(self,index):
        return self.route[index]
    @classmethod
    def E2keep(cls,edges):
        dic={}
        cls.E2K=edges
        if edges:
            for i,j in edges:
                dic[i]=j
                dic[j]=i
        cls.edges2keep=dic
        

##### Functions 
def Distance(i,j,length):
    if i==j:
        return 1000000000000000000
    return length[i,j]
    
    
def get_route(NN,nodes,index):
    route=[]
    for ind in index[0:-1]:
        route.append(nodes[ind])
    route.append(NN+1)
    
    return route
    
def feasible_paths(Data,paths):
    feasible=1
    for p in paths:
        if p.travel_time>Data.Maxtour or p.total_deliveries>Data.Q:
            feasible=0
            break
    return feasible

def change_angle_from_depot(Customers,starting_angel):
    for c in Customers:
         c[1]["AngleWithDepot"] = (c[1]["AngleWithDepot"]+starting_angel) % 360
    return Customers
    
   
    
def Sweep(Data,Customers,starting_angel):
    #Mxtourlenght = Data.Maxtour +100000000
    vehicleCap = Data.Q
    Customers = sorted(Customers, key=lambda x: x[1]["AngleWithDepot"] , reverse=False)
    clusters = list()
    tempCluster = [0]
    cap = 0
    #tour_lenght = 0
    temp_Customers = copy.copy(Customers)
    while len(temp_Customers):
        currCust = temp_Customers.pop(0)
      
        if cap + currCust[1]["delivery"] <= vehicleCap or len(clusters)==Data.M-1: # and tour_lenght + Distance( tempCluster[-1] , currCust[0] ) <= Mxtourlenght :
            tempCluster.append(currCust[0])
            cap += currCust[1]["delivery"]
            #tour_lenght += Distance( tempCluster[-2] , currCust[0] ) # based on shoretst path 
        else:
            clusters.append(tempCluster+[Data.NN+1])
            tempCluster = [0]
            cap = 0
            tempCluster.append(currCust[0])
            cap += currCust[1]["delivery"]
            #tour_lenght += Distance( tempCluster[-2] , currCust[0] )
            
    # print get_distance(DEPOT,Customers[0])
    clusters.append(tempCluster+[Data.NN+1])
 
    return clusters
    
def Optimize(Data,routs,length):
    optimized_routes=[]
    
    NN=Data.NN
    for r in routs:
        if NN+1 in r.route:
            r.remove(NN+1)
        
        if len(r.route)>1:
            route = TSP_model( NN, length ,Route.E2K, Route.edges2avoid ,r )
            Routeobject=Route(route,Data,length)
            Routeobject.set_RDP()
            optimized_routes.append(Routeobject) 
        else:
            optimized_routes.append(r) # this route is [0] and will be deleted in insertation

    
    return optimized_routes
    
def draw_the_solution(Data,paths):
    NN=Data.NN
    testgraph=nx.Graph()
    testgraph.add_nodes_from(range(NN)+[NN+1])
    for r in paths:
        print(r.route)
        print("Route cost:",r.travel_time)
        testgraph.add_path(r.route)
    nx.draw(testgraph)
    plt.show()

def Nodes_selecetion(selected_nodes,edges2keep):
    # This function will select the nodes that connected to selected_nodes by edges2keep
    # Since they should be together in any other route as well, they should move together too
    output=[]
    sets=[]
    
    if edges2keep: 
        list1=[set(e) for e in edges2keep]
        while len(list1):
            To_keep=1
            currentE=list1.pop(0)
            if 0 in currentE: 
                continue
            for e in list1:
                if  currentE & e :
                    list1.append(currentE | e)
                    list1.remove(e)
                    To_keep=0
                    break 
            if To_keep:                          
                sets.append(currentE)    
         
        for n in selected_nodes:
            indi=0
            for s in sets:
                if n in s:
                    output.append( list(s) )
                    indi=1
                    break
            if indi==0:
                output.append([n])

            
    else:
        for n in selected_nodes:
            output.append( [n] )

    return output
    
    
def node2remove(path):
    newtarveltime={}
    for k,n in enumerate(path.route[1:-1]):
        i=k+1
        newtarveltime[n]=path.travel_time-Distance(path.route[i-1],n)-Distance(n,path.route[i+1])+Distance(path.route[i-1],path.route[i+1])
        if newtarveltime[n]<=Data.Maxtour:
            return n
    best_node=min(newtarveltime , key=newtarveltime.get)
    return best_node
    
def Near_me(NN,Ns,P1,length):
    inx={}
    for n in Ns:
        dis_from_N = [ Distance(i,n,length) for i in range(1,NN) ]
        Sorted_inx = np.argpartition(dis_from_N, P1)+1
        inx[n] = Sorted_inx[:P1]
    
    return inx
    
def relocate_edges(paths,edges2keep):
    # This function change the input paths to put two node connected by edges2keep in the same route
    sol=Solution(paths)
    sets=[]
    
    list1=[set(e) for e in edges2keep]
    while len(list1):
        To_keep=1
        currentE=list1.pop(0)
        if 0 in currentE: 
            continue
        for e in list1:
            if  currentE & e :
                list1.append(currentE | e)
                list1.remove(e)
                To_keep=0
                break 
        if To_keep:                          
            sets.append(currentE)
        
    for s in sets:
        S_list=list(s)
        I_inx=sol.Find_the_route( [S_list[0]] )
        for js in S_list:
            if js not in sol.routes[I_inx].route:
                J_inx=sol.Find_the_route( [js] )
                sol.routes[J_inx].remove(js)
                sol.routes[I_inx].route.insert(1,js)
    
    return sol.routes
       
def possible_routes(Data, CurrentSol, V ,Near_nodes):
    Possible_rou_index=[]
    for i , C_route in enumerate( CurrentSol.routes ):
        for v in V:
            if v not in C_route.route and any([k in C_route.route for k in Near_nodes[v]]):
                Possible_rou_index.append(i)
            
        
    if len(CurrentSol.routes)<Data.M:
        Possible_rou_index.append( len(CurrentSol.routes)  )


    if len(Possible_rou_index)==0: #All near node in the same route and reach M
        Possible_rou_index.append( np.random.randint( len(CurrentSol.routes)  ) )
        
    return list(set(Possible_rou_index))
    
    
def TabuRoute(Data,length,Pars,paths):
    it = 1
    q= Pars[0] #Number of Nodes to reassign
    P1 = Pars[1] # number of nearest neighbors of node v
    #P2= Pars[2] # Neighborhood size used in GENI
    Teta_min = Pars[3] # Bounds on the number of iterations for which a move is declared tabu
    Teta_max = Pars[4] # Bounds on the number of iterations for which a move is declared tabu
    G = Pars[5]  # A scaling factor used to define an artificial objective function value
    #H = Pars[6] # The frequency at which updates alpha and beta
    Max_No_Change= Pars[7] # Maximum number of iterations without any improvement
    alpha = 1000
    beta = 1000

    Solution.Data=Data
    CurrentSol=Solution(paths)
    CurrentSol.score_cal(alpha,beta)
    Last_Current = copy.deepcopy(CurrentSol) 
    BestSol = copy.deepcopy(CurrentSol)   
    Last_Best = copy.deepcopy(CurrentSol) 
    Best_F_Sol = copy.deepcopy(CurrentSol)  
    Last_F_Best =  copy.deepcopy(CurrentSol) 
    
    delta=200
    delta_list=[]
    f=np.zeros(Data.NN)
    tabu_list={}
    USconter=0
    No_Change_cont=0
    
    while No_Change_cont <= Max_No_Change:
        
        ## Step 1 Node selection 
        #infeasibility aveare node selection 
        Route_infeasible  = [not r.time_F or not r.cap_F for r in CurrentSol.routes]
        Select_probablity = dict([ (n, Route_infeasible[inx]+1 )  for inx , r in enumerate(CurrentSol.routes)  for n in r.route[1:-1] ] )
        SUM = sum (Select_probablity.values())   
        probablity=[]
        for key in sorted (Select_probablity.keys()):
            probablity.append(Select_probablity[key]/float(SUM) )
            
        
        selected_nodes = np.random.choice(range(1,Data.NN), size=q, p=probablity, replace=False)
        ## consider the edges 2 keep # move the connected node with edges2 keep 
        selected_nodes = Nodes_selecetion(selected_nodes,None)
        # Or use node2remove instead of randomly select the nodes
        ## Step 2 (Evaluationof all candidate moves)
        
        Candidates={}
        for v in selected_nodes:
            Near_nodes = Near_me(Data.NN,v,P1,length) # exclude node 0 
            V_route_inx=CurrentSol.Find_the_route(v)
            possible_routes_ind = possible_routes(Data, CurrentSol,v ,Near_nodes)
            
            for r_id in possible_routes_ind:
                ## [r.route for r in P_Sol.routes]
                ## [length[n,P_Sol.routes[0].route[i+1]] for i,n in enumerate(P_Sol.routes[0].route[:-1])]
                P_Sol = CurrentSol.Inseration_cost(alpha,beta,v,V_route_inx,r_id,length)

                if ( v[0] , r_id ) in tabu_list.keys(): #Check if the move is Tabu
                
                    if (1-P_Sol.feasible)*(P_Sol.score < BestSol.score) or (P_Sol.feasible)*(P_Sol.score < Best_F_Sol.score):
                        Candidates[(v[0],V_route_inx,r_id)]=P_Sol
                else:
                    if P_Sol.score < BestSol.score :
                        name=(v[0],V_route_inx,r_id)
                        Candidates[name]=P_Sol
                    else:
                        P_Sol.score =P_Sol.score + delta* sqrt(Data.M) * G *f[v[0]]
                        name=(v[0],V_route_inx,r_id)
                        Candidates[name]=P_Sol
        
       
        
        # Step 3 Identification of best move
        if len(Candidates)!=0:
            Best_New_Sol=min(Candidates.iteritems(), key= lambda x: x[1].score)

            
            # Step 4 Next current solution
            if Best_New_Sol[1].score > CurrentSol.score and CurrentSol.feasible and USconter==0:
                ## do the US on Bestsol 
                #US=0
                USconter=1
            else:
                USconter=0
                Last_Current = CurrentSol # keep the last sol
                CurrentSol = Best_New_Sol[1] # change the next best sol
                
                #Step 5 Update
                Last_F_Best = Best_F_Sol
                Last_Best = BestSol 
                
                if CurrentSol.feasible and CurrentSol.score<=Best_F_Sol.score:                 
                    Best_F_Sol = CurrentSol # update the best fesibel solution    
                if CurrentSol.score<=BestSol.score:
                    BestSol = CurrentSol #
                    
                f[Best_New_Sol[0][0]]+=1 # update the number of times 5that node v reallocates
                # Add move to the tabu list
                tabu_list[Best_New_Sol[0][0],Best_New_Sol[0][1] ]=it+random.randint(Teta_min,Teta_max)
            
            
        #Update the delta
        delta_list.append( abs(CurrentSol.score-Last_Current.score ) )
        delta=max(delta_list)
        # calculate the no chnage conter 
        if Last_Best.score ==  BestSol.score and Last_F_Best.score ==  Best_F_Sol.score: 
            No_Change_cont += 1
        else:
            No_Change_cont=0
        # update the tabu list
        for i in tabu_list.keys():
            tabu_list[i]-=1
            if tabu_list[i]==0: del tabu_list[i]
        
        #print('Iteration %d : Best solution Obj = %s' %(it,Best_F_Sol.score))
        
        
        it += 1
    #print('Iteration %d : Best F solution Obj = %s But the best obj = %s' %(it,Best_F_Sol.score,BestSol.score))
    return (Best_F_Sol.routes , Best_F_Sol.feasible)
          
##### Main funtion #####

def Initial_feasibleSol(Data2,RDP=None):
    
    
    #if RDP is not None:
    #    Route.Class_RDP=0.8*RDP
        
    global Data
    Data=Data2
    length = Data.distances 

    
    #Data.set_initial_deliveries()
    for n in Data.G.node.values():
        n["delivery"]= min( Data.Q / np.ceil( Data.NN/Data.M ), n["demand"] )
        
    Customers = Data.Gc.nodes.items()
    if RDP is not None:
        for n in Customers:
            n[1]["delivery"]=RDP[n[0]]
    intial_routes = []
    initial_Sol_count=1
    inf_count=0
    while initial_Sol_count <= 1 :
        #for starting_angel in [0,30,60,90,120,150,180,210,240,270]:
        starting_angel=random.randint(0,360)
        Customers=change_angle_from_depot(Customers,starting_angel)
        paths = Sweep(Data,Customers,starting_angel)
        paths = [ Route(p,Data,length) for p in  paths] 
        for p in paths:
            p.set_RDP()

        paths = Optimize(Data,paths,length)
            #draw_the_solution(Data,paths)
         
        if feasible_paths(Data,paths):
            intial_routes += paths
            initial_Sol_count+=1
        else:
            N_of_Node2Change = Data.NN/5
            N_of_near_node = Data.NN/3
            pars = (N_of_Node2Change , N_of_near_node ,None,2,6,0.1,3,20)
            paths,feasible=TabuRoute(Data,length,pars,paths)
            if feasible:
                intial_routes += paths
                initial_Sol_count+=1
                inf_count=0
            else:
                inf_count+=1
        
        if inf_count>=4:
            Route.Class_RDP=0.7*RDP
        if inf_count>=8:
            Route.Class_RDP = 0
            return ([] , 0) 
     
        
    return (intial_routes , 1)       
    
