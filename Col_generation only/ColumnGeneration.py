import itertools as it
import networkx as nx
import random
import numpy as np 
from  feasibleSol import Initial_feasibleSol , Route
from Master import MasterModel
from Sub import SubProblem
from gurobipy import *
import sys



###############################################


def ColumnGen(Data,epsilon):
    NN=Data.NN
    Q=Data.Q  
    G=Data.G
    Gc=Data.Gc
    Gopen=Data.Gopen
    
    
    global RMP_objvals
    RMP_objvals=[]
    
    ####### Initial paths generation  ####### 
  
    initial_routes = Initial_feasibleSol(Data,G,epsilon)   

   ####### Biuld the Master problem #####  
    Paths=initial_routes
    RMP, Y ,(tn,tp)=MasterModel(Data,Paths)
    
    
    ### set varaibles to start the main loop ###
    Subobj=-1
    counter=0
    Pre_Sub_obj=-10
    ############ Main loop ##########
    while Subobj<0.00 or counter <= 8:
                       
        ### Solve the Master problem ####        
        RMP.update()
        RMP.optimize()
        if RMP.status!=2:
             print("Infeasible Master Problem")
        print("Master Problem Optimal Value: %f" %RMP.objVal)
        RMP_objvals.append(RMP.objVal)
        ### Get the dual variables ####
        AllMasterCons=RMP.getConstrs()
        AllDual=RMP.getAttr("Pi",AllMasterCons)
        
        ## stor the Master Problem last solution ##
        
        
        ################### Build and solve Sub Problem ####################
        Sub,x,q ,a = SubProblem(Data, epsilon ,AllDual)
        Sub.optimize()
        ## Check the solution for subtur
        Xv=Sub.getAttr('x',x)
        qv=Sub.getAttr('x',q)
        New_Route=[b[0] for b in Xv.items() if b[1]==1]
        Resulting_G=nx.Graph()
        Resulting_G.add_nodes_from(range(NN))
        for edge in New_Route:
            Resulting_G.add_edge(*edge,Travel_time=G.edges[edge]['Travel_time'])            

        subturs=[c for c in sorted(nx.connected_components(Resulting_G), key=len, reverse=True)]

        # If sub turs are here add constrints until there will be nothing               
        while  len(subturs[1])!=1:
            si=0
            # Ading constraints
            while len(subturs[si])!=1:
                si+=1
                H = G.subgraph(list(subturs[si]))
                complement=[(j,i) for i,j in H.edges() if i!=0 and j!=NN+1] + [(i,j) for i,j in H.edges()] 
                Sub.addConstrs(quicksum(x[i,j] for i,j in complement ) <= quicksum(a[l] for l in subturs[si] if l!=k) for k in subturs[si] )
            # Optimize again
            Sub.optimize()
            Xv=Sub.getAttr('x',x)
            qv=Sub.getAttr('x',q)
            New_Route=[b[0] for b in Xv.items() if b[1]==1]
            Resulting_G=nx.Graph()
            Resulting_G.add_nodes_from(range(NN))
            for edge in New_Route:
                Resulting_G.add_edge(*edge,Travel_time=G.edges[edge]['Travel_time'])            

            subturs=[c for c in sorted(nx.connected_components(Resulting_G), key=len, reverse=True)]

                
        #### cearte the new route and delevery ######
        #New_TravelCost=sum([G.edges[edge]['Travel_time'] for edge in New_Route])
        print("Sub Problem optimal value: %f" %Sub.objVal)
        Subobj = Sub.objVal                
        New_Route=list(set([i for no in New_Route for i in no]))
        New_Route.sort()
        New_Route=Route(New_Route,Data)
        New_RDP = np.zeros(NN)
        New_RDP[New_Route.route[1:-1]] = [ qv[i] for i in New_Route.route[1:-1] ]
        New_Route.set_RDP(list(New_RDP))
    
        ## Update path
        Paths.append(New_Route)

        ## update the counter
        if Pre_Sub_obj==Subobj:
            counter+=1
        Pre_Sub_obj=Subobj
        
        ###  Update the Master problem  ##
        col=Column()
        nodes_not_inRoute=list( set(range(1,NN)) - set(New_Route.route[1:-1]) )
        for i,j in it.permutations(New_Route.route[1:-1],2):
            cons=RMP.getConstrByName("linear[%d,%d]" %(i,j))
            col.addTerms(New_Route.RDP[i]-New_Route.RDP[j],cons)
            
        for n in New_Route.route[1:-1]:
            #### Master problem linear constrint update ##
            index=zip( [n]*len( nodes_not_inRoute ) , nodes_not_inRoute )
            for i,j in index:
                cons=RMP.getConstrByName("linear[%d,%d]" %(i,j))
                col.addTerms(New_Route.RDP[n],cons)
                    
            index=zip( nodes_not_inRoute , [n]*len( nodes_not_inRoute ) )
            for i,j in index:
                cons=RMP.getConstrByName("linear[%d,%d]" %(i,j))
                col.addTerms(-1*New_Route.RDP[n],cons)
                
            ### mater problem visit consrtiant update ###
            consvisit=RMP.getConstrByName("visit[%d]" %n )
            col.addTerms(1,consvisit)
        ### vehicel constriant ###
        cons=RMP.getConstrByName("vehicle" ) 
        col.addTerms(1,cons)
        ### Inv constrint ###
        cons=RMP.getConstrByName("Inv" ) 
        col.addTerms(sum(New_Route.RDP),cons)
        
        RMP.addVar(lb=0,ub=1,name="y[%d]" %len(Paths), column=col )
            
   
        
    ## read the final selected Y variables 
    Yv=RMP.getAttr('x',Y)
    '''
    tnv=RMP.getAttr('x',tn)
    tpv=RMP.getAttr('x',tp)
    print(sum(tnv.values()))
    print(sum(tpv.values()))
    '''    
    selected_route_id=[b[0] for b in Yv.items() if b[1]==1]
    Selected_Routes=[Paths[i] for i in selected_route_id]
    Real_Routes=[a.route for a in Selected_Routes]
    Real_RDP =[a.RDP[i] for a in Selected_Routes for i,node in enumerate(a.RDP) if node > 0]
    print(Real_Routes)
    print(Real_RDP)
    return(RMP_objvals[-1])