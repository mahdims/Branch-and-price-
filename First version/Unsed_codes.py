# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 14:28:10 2019

@author: User
"""
   def Rounding(self):
        self.Round_RDP= np.sum([np.array(self.Col_dic[k].RDP)*self.Y[k] for k in self.Col_dic.keys()],axis=0)
        
        selected_routes = copy.copy(self.selected_route)
        candidate_routes=[]
        while len(selected_routes):
            route = selected_routes.pop(0)
            inx=[ i for i,a in enumerate(self.selected_route) if a==route]
            Y=sum( [self.Y[ self.selected_R_D[i] ] for i in inx ] )
            candidate_routes.append(  (Y*(len(route))**1.5,route)  )
            while 1:
                try:
                     selected_routes.remove(route)
                except:
                     break 
        candidate_routes=sorted(candidate_routes,key=lambda x:x[0],reverse=True)  

        Final_routes=[]
        while len(Final_routes) < Node.Data.M and len(candidate_routes):
            Final_routes.append( candidate_routes.pop(0)[1] )
            for i in Final_routes[-1][1:-1]:
                temp=copy.copy( candidate_routes )
                for y,r in temp:
                    if i in r:
                        candidate_routes.remove( (y,r) )
        
        for it in range(1,Node.Data.NN):
            if not any([it in r for r in Final_routes]):
                Final_routes=sorted(Final_routes,key=len,reverse=False)
                Final_routes[0].insert(1,it)
        
        paths=[]
        Route.Class_RDP=self.Round_RDP
        for r in Final_routes:
            RR=Route(r,Node.Data)
            RR.set_RDP()
            paths.append(RR)            
        
        pars = ( Node.Data.NN/5 , Node.Data.NN/3 ,None,2,6,0.1,3,20)
        paths,feasible=TabuRoute(Node.Data,Node.epsilon,None,pars,paths)
        if feasible:
            print("Rounding objective")
            Obj_Calc( Node.Data , self.Y , self.Col_dic )



# 
def TSP(node2visit,NN):
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
    route = get_route(NN,node2visit,route_list)
    return route