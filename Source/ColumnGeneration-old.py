import itertools as it
import networkx as nx
import numpy as np 
from  feasibleSol import Route
from itertools import *
from gurobipy import *
import copy
import sys
import matplotlib as matp

###############################################
def subtourelim(model, where):
  if where == GRB.callback.MIPSOL:
    selected = []
    sol={}
    # make a list of edges selected in the solution
    for i,j in model._varX.keys():
        sol[i,j] = model.cbGetSolution(model._varX[i,j])
        if sol[i,j] > 0.5:
            selected.append( (i,j) )
    # find the shortest cycle in the selected edge list
    tour= Get_the_Subtours(G,selected)
    if tour:
      # add a subtour elimination constrain
        complement=[i for i in permutations(tour,2)] # if just one node gives it will return empty list []
        complement2=copy.copy(complement)
        for e in complement: 
            if e not in model._varX.keys():
                complement2.remove(e)
                
        expr1 = 0
        for i,j in complement2:
            expr1 += model._varX[i,j]
        for k in tour:
            expr2=0
            for l in tour :
                if l!=k:
                    expr2+=model._varA[l]
                    
            model.cbLazy(expr1 <= expr2)

      
def Get_the_Subtours(G,edges):
    NN=G.number_of_nodes()-1
    nodes= set()
    for e in edges:
        nodes=nodes|set(e)
        
    Resulting_G=nx.Graph()
    Resulting_G.add_nodes_from(nodes)
 
    for e in edges:
        Resulting_G.add_edge( *e  ) 
   
    subtours=[c for c in sorted(nx.connected_components(Resulting_G), key=len, reverse=True)]
    # Put the tour with depot nodes at first
    for s in subtours:
        if 0 in s and NN+1 in s:
            subtours.remove(s)
    if subtours:
        return list( subtours[subtours.index(min( subtours , key=lambda x :len(x) ) ) ]) # return minim length sub ture
    else:
        return []
    
def get_Duals(NN , RMP):
    AllMasterCons=RMP.getConstrs()
    AllDual=RMP.getAttr("Pi",AllMasterCons)
    
    linear=np.array(AllDual[0:(NN-1)*(NN-1)]).reshape((NN-1,NN-1)) #get_constraints(RMP, name='linear')
    Per_end=(NN-1)*(NN-1)    
    totaltime= np.array(AllDual[Per_end])
    visit=np.array(AllDual[Per_end+1:Per_end+NN])
    Per_end =  Per_end+NN
    vehicle=np.array(AllDual[Per_end])
    Inv=np.array(AllDual[Per_end+1])
    
    return (AllDual, linear, totaltime,visit , vehicle ,Inv )    

def Set_sub_obj(Data,R,Gc,dis,Duals,edges2keep,(Sub,x,q,a)):
    NN=len(a)-1
    (AllDual, linear, totaltime ,visit , vehicle ,Inv ) = Duals
    Gc=G.subgraph(range(1,NN))
    #complement= [i for i in permutations(Gc.nodes,2)] + [(0,i) for i in Gc.nodes] +[(i,NN+1) for i in Gc.nodes]
    
    if edges2keep:
        Per_end =  (NN-1)*(NN-1)+NN+2
        E_keep=np.array(AllDual[Per_end : ])
        Sub.setObjective(-quicksum((q[i]*Gc.node[j]['demand']-q[j]*Gc.node[i]['demand'])*linear[i-1,j-1] for i in Gc.nodes for j in Gc.nodes)   
        - quicksum(a[i]*visit[i-1] for i in Gc.nodes)
        - quicksum(q)*(Inv+1)-vehicle
        - quicksum(x[i,j]*dis[(i,j)] for (i,j) in x.keys() if j!=NN+1) *(totaltime + Data.Gamma/R)
        - quicksum( (x[j,i])*E_keep[k] for k,(i,j) in enumerate(edges2keep) if i!=0 and j!=NN+1  )
        - quicksum( (x[i,j])*E_keep[k] for k,(i,j) in enumerate(edges2keep) )
        , GRB.MINIMIZE)
    else:
        Sub.setObjective(-quicksum((q[i]*Gc.node[j]['demand']-q[j]*Gc.node[i]['demand'])*linear[i-1,j-1] for i in Gc.nodes for j in Gc.nodes)   
                    - quicksum(x[i,j]*dis[(i,j)] for (i,j) in x.keys() if j!=NN+1) *(totaltime + Data.Gamma/R)                   
                    - quicksum(a[i]*visit[i-1] for i in Gc.nodes)
                    - quicksum(q)*(Inv+1)-vehicle
                     , GRB.MINIMIZE)
    
    return Sub

def build_the_route(Data,New_Route,dis):
    Edges=copy.copy(New_Route)
    PerNode=0
    route=[0]
    while Edges :
        for e in Edges :
            if PerNode in e:
                break
        route.append(e[1])
        PerNode = e[1]
        Edges.remove(e)
        
    New_Route=Route(route,Data,dis)
    return New_Route
def Solve_pricing_heuristically(Data, R, Duals , edges2keep):
    G=Data.G
    
    
def Solve_pricing_exactly(Data,R,Duals,edges2keep,(Sub,x,q,a)):
    ## Set the sub probolem  objective 
    Gc = Data.Gc
    dis = Data.distances
    NN = Data.NN
    Sub = Set_sub_obj(Data,R,Gc,dis,Duals,edges2keep,(Sub,x,q,a))
    
    ### Solve Sub Problem
    Sub.optimize(subtourelim)
    if Sub.status!=2:
        # sub problem is infeasible !! the only reseon maybe the graph is not connected !! really???
        print(" 1 - Infeasible Subproblem Problem")
        return (0,Data.BigM,[],Col_dic)
        
    ### get the subproblem solution 
    Xv=Sub.getAttr('x',x)
    qv=Sub.getAttr('x',q)
    
    #### cearte the new route - delivery ######
    Selected_edges=[e for e,value in Xv.items() if value > 0.5]
    New_Route = build_the_route(Data , Selected_edges,dis)
    New_RDP   = np.zeros(NN)
    
    New_RDP[New_Route.route[1:-1]] = [ qv[i] for i in New_Route.route[1:-1] ]
    New_Route.set_RDP(list(New_RDP))
    
    #print("Sub Problem optimal value: %f" %Sub.objVal)
    Subobj = Sub.objVal  
    
    return New_Route , Subobj
    
def Add_the_columns(Data , R , Col_dic , RMP , edges2keep, New_Route):
    Gc=Data.Gc   
    Gamma=Data.Gamma
    col=Column()         

    for i,j in it.permutations(Gc.nodes(),2):
        #### Master problem linear constrint update ##
        cons=RMP.getConstrByName("linear[%d,%d]" %(i,j))
        col.addTerms(- New_Route.RDP[j]*Gc.node[i]['demand'] + New_Route.RDP[i]*Gc.node[j]['demand'],cons)
        
    for n in New_Route.route[1:-1]:
        consvisit=RMP.getConstrByName("visit[%d]" %n )
        col.addTerms(1,consvisit)
  
    ### total time epsilon constraint ##
    cons=RMP.getConstrByName("Total_time")
    col.addTerms(New_Route.travel_time ,cons)          
    ### vehicel constriant ###
    cons=RMP.getConstrByName("vehicle" ) 
    col.addTerms(1,cons)
    ### Inv constrint ###
    cons=RMP.getConstrByName("Inv" ) 
    col.addTerms(sum(New_Route.RDP),cons)
    ### edges 2 keep
    if edges2keep:
        prenode=0
        Selected_edges=[]
        for i in New_Route.route[1:]:    
            Selected_edges.append( (prenode,i) )
            prenode = i
        
        for i,j  in edges2keep:
            cons=RMP.getConstrByName("edge2keep[%d,%d]" %(i,j))
            col.addTerms((i,j) in Selected_edges or (j,i) in Selected_edges ,cons)
            
            
    newY_inx = max(Col_dic.keys()) + 1
    RMP.addVar(lb=0,ub=1,obj=-sum(New_Route.RDP)-Gamma*New_Route.travel_time/R,
               name="y[%d]" %(newY_inx), column=col )
    RMP.update()
    # Update path
    Col_dic[newY_inx] = copy.copy(New_Route) 
    
    
    return RMP , Col_dic
    
    
def ColumnGen(Data,R,RMP,G_in,Col_dic,dis,edges2keep,(Sub,x,q,a)):
    Stoping_R_cost=-0.1
    global G ,Gamma
    G=G_in
    NN=Data.NN
    Gamma=Data.Gamma
    RMP_objvals=[] # A list to have all objvals
    ## set varaibles to start the main loop ###
    Subobj=-1
    counter=0
    Pre_Sub_obj=-10
    ############ Main loop ##########
    while Subobj< Stoping_R_cost: # Stoping critira !
        ### Solve the Master problem        
        RMP.optimize() 
        if RMP.status!=2:
             # Report that the problem in current node is infeasible
             print("Infeasible Master Problem")
             return (0,Data.BigM,[],Col_dic)
        #print("Master Problem Optimal Value: %f" %RMP.objVal)
        RMP_objvals.append(RMP.objVal)
        ## Get the dual variables
        Duals = get_Duals(NN , RMP)
        ## Solve the sub probolem   
        New_Route , Subobj =  Solve_pricing_exactly(Data,R,Duals,edges2keep,(Sub,x,q,a))       
        ## update the counter
        if Pre_Sub_obj==Subobj:
            counter+=1
            print(counter)
        Pre_Sub_obj=Subobj
        
        if Subobj>Stoping_R_cost : 
            continue
        ###  Update the Master problem  ##
        RMP, Col_dic = Add_the_columns(Data , R , Col_dic , RMP , edges2keep, New_Route)

    
    ## read the final selected Y variables 
    Y=dict([( int(var.VarName.split('[')[1].split(']')[0])  ,  var.X ) for var in RMP.getVars() if var.VarName.find('y') != -1])
    #print("Master Problem Optimal Value: %f" %RMP.objVal)

    return(1,RMP_objvals[-1],Y, Col_dic)