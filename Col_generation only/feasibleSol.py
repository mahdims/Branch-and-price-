import random
import numpy as np
import copy
import networkx as nx
import matplotlib.pyplot as plt
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
from math import sqrt
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
            route.Feasiblity( Solution.Data,Solution.epsilon )
            violated_time += route.time_feasibility
            violated_cap  += route.cap_feasibility
            total_time    += route.travel_time
        self.time_feasible = violated_time == 0
        self.cap_feasible = violated_cap == 0
        self.feasible = self.time_feasible and self.cap_feasible
        self.score = total_time + alpha*violated_time + beta*violated_cap
        
        
    def Find_the_route(self,v):
        
        for i,r in enumerate(self.routes):
            if v in r.route:
                return i
    def Replace(self,route_inx,New_route)   :
        self.routes[route_inx]=New_route
    
    def Inseration_cost(self,alpha,beta,node,node_route,des_route):
        NewSol=copy.deepcopy(self)
        
        NewSol.routes[node_route].route.remove(node)
        NewSol.routes[node_route] = Optimize( Solution.Data , [NewSol.routes[node_route].route[:-1]] )[0]
        
        if des_route < len(NewSol.routes):
            
            NewSol.routes[des_route].route.insert(-1,node)
            NewSol.routes[des_route]= Optimize( Solution.Data , [NewSol.routes[des_route].route[:-1]] )[0]
        else:
            newpath = Route([0,node,Solution.Data.NN+1],Solution.Data)
            newpath.set_RDP()
            NewSol.routes.append(newpath)
        
        NewSol.score_cal(alpha,beta)
        return NewSol
        
            

class Route():
    
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
        for n in self.route[1:]: # travel time calculation
            if n==Data.NN+1:
                break
            Travelcost +=  Data.distances[PreNode,n]
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
        self.time_feasibility = max(0,self.travel_time-epsilon)
        self.cap_feasibility = max(0, self.total_deliveries-Data.Q)
    
    def remove(self,v):
        self.route.remove(v)
        
    def __getitem__(self,index):
        return self.route[index]
        
    

##### Functions 
def Distance(i,j):
    if i==j:
        return 1000000000000000000
    return length[i,j]
    
    
def get_route(Data,nodes,index):
    route=[]
    for ind in index[0:-1]:
        route.append(nodes[ind])
    route.append(Data.NN+1)
    
    return route
    
def feasible_paths(Data,epsilon,paths):
    feasible=1
    for p in paths:
        if p.travel_time>epsilon or p.total_deliveries>Data.Q:
            feasible=0
            break
    return feasible

def change_angle_from_depot(Customers,starting_angel):
    for c in Customers:
         c[1]["AngleWithDepot"] = (c[1]["AngleWithDepot"]+starting_angel) % 360
    return Customers
    
def TSP(node2visit):
    size=len(node2visit)
    def Dis(i,j):
        a=node2visit[i]
        b=node2visit[j]
        return int(length[a,b])
  # Create routing model
    route_list = []
    if size > 0:
        # Nodes are indexed from 0 to parser_tsp_size - 1, by default the start of
        # the route is node 0.
        routing = pywrapcp.RoutingModel(size, 1, 0)

        search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
        # Setting first solution heuristic (cheapest addition).
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.BEST_INSERTION)

        routing.SetArcCostEvaluatorOfAllVehicles(Dis)
        # Forbid node connections (randomly).
        #rand = random.Random()
        #rand.seed(0)

        assignment = routing.Solve()
        if assignment:
            # Solution cost.
            #print(assignment.ObjectiveValue())
            # Inspect solution.
            # Only one route here; otherwise iterate from 0 to routing.vehicles() - 1
            route_number = 0
            node = routing.Start(route_number)
            #route = ''
            while not routing.IsEnd(node):
                #route += str(node) + ' -> '
                route_list.append(node)
                node = assignment.Value(routing.NextVar(node))
            #route += '0'
            route_list.append(0)
            # print(route)
        else:
            print('No solution found.')
            return -1
    return route_list
    

    
    
    
def Sweep(Data,Customers,epsilon,starting_angel):
    #Mxtourlenght = epsilon +100000000
    vehicleCap = Data.Q
    Customers = sorted(Customers, key=lambda x: x[1]["AngleWithDepot"] , reverse=False)
    clusters = list()
    tempCluster = [0]
    cap = 0
    #tour_lenght = 0
    temp_Customers = copy.copy(Customers)
    while len(temp_Customers):
        currCust = temp_Customers.pop(0)
      
        if cap + currCust[1]["delivery"] <= vehicleCap: # and tour_lenght + Distance( tempCluster[-1] , currCust[0] ) <= Mxtourlenght :
            tempCluster.append(currCust[0])
            cap += currCust[1]["delivery"]
            #tour_lenght += Distance( tempCluster[-2] , currCust[0] ) # based on shoretst path 
        else:
            clusters.append(tempCluster)
            tempCluster = [0]
            cap = 0
            tempCluster.append(currCust[0])
            cap += currCust[1]["delivery"]
            #tour_lenght += Distance( tempCluster[-2] , currCust[0] )
            
    # print get_distance(DEPOT,Customers[0])
    clusters.append(tempCluster)
 
    return clusters
    
def Optimize(Data,routs):
    optimized_routes=[]
    for r in routs:
        route = TSP( r )
        # print route
        route = get_route(Data,r,route)
        Routeobject=Route(route,Data)
        #print ("#### after TSP ####")
        #print(route)
        #print(Routeobject.travel_time)
        Routeobject.set_RDP()
        optimized_routes.append(Routeobject) 

    
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

def node2remove(path):
    newtarveltime={}
    for k,n in enumerate(path.route[1:-1]):
        i=k+1
        newtarveltime[n]=path.travel_time-Distance(path.route[i-1],n)-Distance(n,path.route[i+1])+Distance(path.route[i-1],path.route[i+1])
        if newtarveltime[n]<=Epsilon:
            return n
    best_node=min(newtarveltime , key=newtarveltime.get)
    return best_node
    
def Near_me(NN,n,P1):

    dis_from_N=[ Distance(n,i) for i in range(NN) ]
    inx=np.argpartition(dis_from_N, P1)
    
    return inx[:P1]
    
def possible_routes(Data, CurrentSol,v ,Near_nodes):
    Possible_rou_index=[]
    for i , C_route in enumerate( CurrentSol.routes ):
        if v not in C_route.route and any([k in C_route.route for k in Near_nodes]):
            Possible_rou_index.append(i)
            
        
    if len(CurrentSol.routes)<Data.M:
        Possible_rou_index += range(len(CurrentSol.routes),Data.M)
        
    return Possible_rou_index
    
    
def TabuRoute(Data,epsilon,Pars,paths):
    it = 1
    q= Pars[0] #Number of Nodes to reassign
    P1 = Pars[1] # number of nearest neighbors of node v
    P2= Pars[2] # Neighborhood size used in GENI
    Teta_min = Pars[3] # Bounds on the number of iterations for which a move is declared tabu
    Teta_max = Pars[4] # Bounds on the number of iterations for which a move is declared tabu
    G = Pars[5]  # A scaling factor used to define an artificial objective function value
    H = Pars[6] # The frequency at which updates alpha and beta
    Max_No_Change= Pars[7] # Maximum number of iterations without any improvement
    alpha = 1000
    beta = 1000
    
    Solution.epsilon=epsilon
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
        selected_nodes = np.random.choice(range(1,Data.NN), size=q, replace=False)
        # Or use node2remove instead of randomly select the nodes
        ## Step 2 (Evaluationof all candidate moves)
        Candidates={}
        for v in selected_nodes:
            Near_nodes = Near_me(Data.NN,v,P1)
            V_route_inx=CurrentSol.Find_the_route(v)
            possible_routes_ind = possible_routes(Data, CurrentSol,v ,Near_nodes)
            
            for r_id in possible_routes_ind:
                
                P_Sol = CurrentSol.Inseration_cost(alpha,beta,v,V_route_inx,r_id)

                if (v,r_id) in tabu_list.keys(): #Check if the move is Tabu
                
                    if (1-P_Sol.feasible)*(P_Sol.score < BestSol.score) or (P_Sol.feasible)*(P_Sol.score < Best_F_Sol.score):
                        Candidates[(v,V_route_inx,r_id)]=P_Sol
                else:
                    if P_Sol.score < BestSol.score :
                        Candidates[(v,V_route_inx,r_id)]=P_Sol
                    else:
                        P_Sol.score =P_Sol.score + delta* sqrt(Data.M) * G *f[v]
                        Candidates[(v,V_route_inx,r_id)]=P_Sol
        
       
        
        # Step 3 Identification of best move
        if len(Candidates)!=0:
        
            Best_New_Sol=min(Candidates.iteritems(), key= lambda x: x[1].score)
            
            
            # Step 4 Next current solution
            if Best_New_Sol[1].score > CurrentSol.score and CurrentSol.feasible and USconter==0:
                ## do the US on Bestsol 
                US=0
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
        
        print('Iteration %d : Best solution Obj = %s' %(it,Best_F_Sol.score))
        
        
        it += 1
    
    return (Best_F_Sol.routes , Best_F_Sol.feasible)
            
############ Main funtion 
def Initial_feasibleSol(Data,G,epsilon):

    global length
    length = Data.distances
    global Epsilon
    Epsilon=epsilon
    
    Data.set_initial_deliveries()
    Customers = Data.Gc.nodes.items()
    intial_routes = []
    initial_Sol_count=1
    while initial_Sol_count <= 2 :
    #for starting_angel in [0,30,60,90,120,150,180,210,240,270]:
        starting_angel=random.randint(0,360)
        Customers=change_angle_from_depot(Customers,starting_angel)
        paths = Sweep(Data,Customers,epsilon,starting_angel)
        paths = Optimize(Data,paths)
        #draw_the_solution(Data,paths)
        
        if feasible_paths(Data,epsilon,paths):
            intial_routes += paths
            initial_Sol_count+=1
        else:
            N_of_Node2Change = Data.NN/5
            N_of_near_node = Data.NN/3
            pars = (N_of_Node2Change , N_of_near_node ,None,2,6,0.1,3,20)
            paths,feasible=TabuRoute(Data,epsilon,pars,paths)
            if feasible:
                intial_routes += paths
                initial_Sol_count+=1
                
    return intial_routes        
    
    
    
    
    
    
    
    
    
    