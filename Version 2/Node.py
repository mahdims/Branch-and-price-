from feasibleSol import Initial_feasibleSol ,Route , TabuRoute
from ColumnGeneration import ColumnGen
from Master import MasterModel
from Sub import SubProblem
from Obj_Calc import Obj_Calc
from Master_int import Master_int
from time import time 
import copy
import sys
import itertools as it 
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

def edge_in_route(edge,route): # there is a copy of this functin Master.py -- Change Together 
    # This function will check if route use edge i-j or not
    i=edge[0]
    j=edge[1]
    
    indicator=0
    if i in route and j in route :
        I_inx=np.where(np.array(route)==i)[0][0]
        if I_inx==0 and route[1]==j: return 1
        if I_inx==len(route)-1 and route[-2]==j: return 1
        if  I_inx!=0 and I_inx!=len(route)-1:
            if route[I_inx+1]==j or route[I_inx-1]==j:
                indicator=1
    return indicator

def calculate_the_obj(Data, R, Routes,RDPs):
    Gc = Data.Gc
    # create the mapping to find the node quantities  :))
    Q_mapping ={}
    for i in Gc.nodes :
        for r_ID, route in enumerate(Routes):
            inx = np.where(np.array(route.route) == i)[0]
            if len(inx) != 0:
                inx = inx[0]
                break
        Q_mapping[i] = (r_ID,inx)

    part1 =0
    for i in Gc.nodes :
        (r_ID, inx) = Q_mapping[i]
        part1 += Gc.node[i]['demand'] - RDPs[r_ID][inx]

    part2  = 0
    for i,j in it.product(Gc.nodes, Gc.nodes):
        (r_IDi, inxi) = Q_mapping[i]
        (r_IDj, inxj) = Q_mapping[j]
        part2 += abs(Gc.node[j]['demand']*RDPs[r_IDi][inxi] - Gc.node[i]['demand']*RDPs[r_IDj][inxj])

    part2 = (Data.Lambda / Data.total_demand) * part2
    part3 = Data.Gamma * (Data.Total_dis_epsilon - sum([r.travel_time for r in Routes])) / R

    return(part1+part2+part3)


class Node():
    best_obj = float("Inf")
    best_node= None
    best_Route=[]
    best_RDP=[]
    LowerBound = 0
    Node_dic = {0:[]}
    Node_dic2={}
    NodeCount=0
    Data=None
    R=None
    Tree=nx.Graph()
    
    def __init__(self, ID,PID ,level, pos ,Col_dic,G,edge2keep= [] ,edge2avoid= [] ,Initial_RDP=None):
        
        self.level=level
        self.ID=ID
        self.Parent_ID = PID
        self.pos=pos
        self.Col_dic = Col_dic
        self.G = G
        self.edges2keep=edge2keep
        self.edge2avoid=edge2avoid
        self.Objval = None
        self.selected_R_D = []
        self.selected_route = []
        self.feasible = self.check_G_feasibility()
        self.Dis=Node.Data.distances        
        # solve the node - proccessing 
        if self.feasible :
            self.Col_dic_update(Initial_RDP) # will add feasible solutions to the Col Dic by initial heuristic
            if self.feasible:
                self.solve() # solve with column generation
                self.Upper_bound_finder()

        # Extra information (Save the nodes and compelet the tree fro drawings)
        Node.NodeCount += 1
        '''        
        Node.Node_dic2[self.ID] = self
        if level < len (Node.Node_dic):
            Node.Node_dic[level].append(self)
        else:
            Node.Node_dic[level]=[self]
        '''
        Node.Tree.add_node(self.ID)
        Node.Tree.add_edge(  self.Parent_ID , self.ID  )

    def Upper_bound_finder(self):
        self.Int_Objval, self.Int_route, self.Int_RDP = Master_int(Node.Data, Node.R, Node.best_obj, self.Col_dic)


        # replace the new routes with

    def check_G_feasibility(self):
        # This function performs three feasiblity test on the graph

        # if the graph is still conected 
        subturs=[c for c in sorted(nx.connected_components(self.G), key=len, reverse=True)]
        if len(subturs)!=1:
            return 0 # Graph became disconnected 

        # more then two must visited edges are connected to one node
        G2=nx.Graph()
        G2.add_nodes_from(self.G.nodes())
        G2.add_edges_from(self.edges2keep)
        
        for i in G2.nodes():
            if G2.degree(i)>=3:
                return 0

        # the degree of depot node shouldn't larger than number of vehicles
        if G2.degree(0) > Node.Data.M:
            return 0

        # every cycle should have depot inside
        cycles = nx.cycle_basis(G2)
        for c in cycles:
            if 0 not in c:
                return 0

        # there is no edge edge to branch
        edgeset = list(self.G.edges())
        for n in self.G.node:
            if n!=0 and n!= Node.Data.NN+1 :           
                edgeset.remove((n , Node.Data.NN+1))
        #print("Number of existed edges: %s" %(len(edgeset)-Node.Data.NN+1))
        if edgeset == []:
            return 0
        return 1
        
    
    def Update_shortest_dis(self):
        # change the dis matrix to avoid deleted edges in initial heuristic
        # This is needed for left nodes and the nodes under them
        # We use bellman ford algorithm to find al pair shorets beased on new Graph
        #Dis=nx.all_pairs_bellman_ford_path_length(self.G  ,  weight='Travel_time')
        
        paths = dict(nx.all_pairs_bellman_ford_path(self.G))
        for i,j in it.combinations(self.G.node,2):
            path=paths[i][j]
            travel_dis=0
            pernode=path.pop(0)
            while len(path):
                Cnode = path.pop(0)
                travel_dis += self.G.edges[pernode,Cnode]["Travel_distance"]
                pernode = Cnode
            self.Dis[i,j] = travel_dis
            self.Dis[j,i] = travel_dis

    def Col_dic_update(self,RDP):
        # This function Generates some new R_D according to new dis (edges to avoid)
        New_Col, self.feasible = Initial_feasibleSol(Node.Data,self.G,edges2keep=self.edges2keep,edges2avoid=self.edge2avoid,RDP=RDP)
        if not self.feasible:
            print("Initial heuristic say Infeasible")
        # Add the newly generated columns to the Col_dic
        for R_D in New_Col:
            unique, inx = R_D.Is_unique(self.Col_dic)
            if unique == 1:
                self.Col_dic[inx] = copy.copy(R_D)
            elif unique == 2:
                self.Col_dic[inx].add_RDP(R_D.RDP[1])
            elif unique == 3:
                pass
        del New_Col

    def solve(self):
        # solve a node (integer relaxtion) by column generation 
        # Build the master problem 
        RMP = MasterModel(Node.Data,self.Col_dic , Node.R ,self.edges2keep)
        
        # Build the sub-problem only the constraints and variables 
        Sub , x , q , a = SubProblem( Node.Data , self.G , self.Dis ,self.edges2keep ,  self.edge2avoid )

        sub=(Sub ,x , q , a)

        ######### run the Column genearation ########
        start=time()
        (self.feasible, self.Objval, self.Y, self.Col_dic) = ColumnGen(Node.Data,Node.R,RMP,self.G,self.Col_dic,self.Dis,self.edges2keep, self.edge2avoid,sub)
        self.Col_runtime=time()-start

        if self.feasible: # find the used route-deliveries
            self.selected_R_D = [a for a in self.Y.keys() if self.Y[a] != 0]
            #self.selected_route = [self.Col_dic[i].route  for i,j in self.selected_R_D]
            #self.Rounding()
            #self.Round_RDP= np.sum([np.array(self.Col_dic[k].RDP)*self.Y[k] for k in self.Col_dic.keys()],axis=0)
            #self.Round_RDP =np.array([round(a,4) for a in self.Round_RDP] )

    def Strong_Branching(self) :
        # Find the branching rule
        Edge_Val={}
        # calculate the xij values ***** Not for   i--NN+1 ******
        
        for edge in self.G.edges():
            if Node.Data.NN+1 not in edge: #Do not branch on i-NN+1 edges
                Edge_Val[edge]= abs( sum([ edge_in_route(edge , self.Col_dic[Col_ID].route)* self.Y[Col_ID,RDP_ID] for Col_ID,RDP_ID in self.selected_R_D ]) - 0.5)

        # find the one with\ the minimum 
        
        while 1 :
            selected_edge= min(Edge_Val , key=Edge_Val.get)
            if selected_edge in self.edge2avoid + self.edges2keep:
                del Edge_Val[selected_edge]
            else:
                break

        counter = 0
        for key,val in Edge_Val.items():
            if val <=  1.1 * Edge_Val[selected_edge]:
                counter += 1
        print("I select the branching edges among %d alternative randomly!!" %counter)


        L_Node = self.Arc_Branching("left",*selected_edge)
        R_Node = self.Arc_Branching("right",*selected_edge)
        
        return [L_Node, R_Node ]
        
        
        
    def Arc_Branching(self,WhichNode,i,j):
        # This function will branch on given edge and generates 2 child nodes
        
        Col_dic=copy.copy(self.Col_dic)
        G=copy.deepcopy(self.G)
        
        if WhichNode == "left":
            # update the set columns by removing edge i-j or j-i
            for inx , R_D in self.Col_dic.items():
                if edge_in_route( (i,j) , R_D.route ):
                    #RMP.remove( RMP.getVarByName('y[%d]'%inx) )
                    del Col_dic[inx]
                    
            # update the graph as well
            G.remove_edge(i,j)  
            
            edge2avoid = copy.copy(self.edge2avoid)
            edge2avoid.append( (i,j) )

            return Node( Node.NodeCount, self.ID , self.level+1 ,WhichNode , Col_dic, G, edge2avoid = edge2avoid , edge2keep=self.edges2keep  )

        elif WhichNode == "right":
            
            new_cols={} #jsut keep the RD that have i-j or j-i Ot niether of them 
            for inx , R_D in Col_dic.items():
                if i in R_D.route or j in R_D.route:
                    if edge_in_route( (i,j) ,R_D.route):## check if it have either for i-j and j-i
                        new_cols[inx] = R_D
                    else:
                        if i==0 and j not in R_D.route:  #If i is 0 and j is not in route  
                            new_cols[inx] = R_D   
                else: #IF the route do not have both i and j 
                    new_cols[inx] = R_D
        
            Col_dic=new_cols
            edges2keep = copy.copy(self.edges2keep)
            edges2keep.append( (i,j) )
            
            return Node( Node.NodeCount  , self.ID , self.level+1 ,WhichNode , Col_dic, G, edge2keep = edges2keep, edge2avoid=self.edge2avoid  )

    
    def integer(self):
        # This function checks if all master problem variables are integer or not
        if self.feasible:
            indictor = all ( [ int(self.Y[i]) == self.Y[i]  for i in self.Y.keys() ] )
        else:
            indictor = False
        
        return indictor
    
    def delete(self):
        del self.G
        del self
        
    
    @classmethod
    def Draw_the_tree(cls):
        # This function draws the Branch and bound tree 
        W=100
        label_dic={} # lable dictionery 
        pos={} # node position dictionery
        x={0:W/2}
        y={}
        color_map=[]
        maxlevel= len(Node.Node_dic)
        Ystep=W/maxlevel
        for le in range( maxlevel ):
            NfNodes= len( Node.Node_dic[le] )
            Xstep  = W/4*NfNodes
            Node.Node_dic[le]=sorted(Node.Node_dic[le], key=lambda x: x.Parent_ID)
            for inx,n in enumerate(Node.Node_dic[le]):
    
                if n.pos=="left":
                    x[n.ID] = x[Node.Node_dic2[n.Parent_ID].ID] - Xstep
                elif n.pos=="right":
                    x[n.ID] = x[Node.Node_dic2[n.Parent_ID].ID] + Xstep
                else:
                    x[n.ID] = x[Node.Node_dic2[n.Parent_ID].ID]
              
                y[n.ID] = 100 - Ystep * n.level
                pos[n.ID]= (x[n.ID],y[n.ID])
                if not n.feasible:
                    label_dic[n.ID]= "IF-%d " %n.ID
                elif n.integer():
                    label_dic[n.ID]= "IN-%d \n %s" % ( n.ID , round( n.Objval , 1) )
                else:
                    label_dic[n.ID]= "%d-%d" %(n.ID,round( n.Objval , 1) )
                    
        
        '''
        for n in Node.Node_list:
            if not n.feasible:
                color_map.append('red')
            elif n.integer:
                color_map.append('green')
            else:
                color_map.append('blue')
        '''     
           
        plt.title("Branch and price tree")
        
        nx.draw(Node.Tree, node_size=700,  node_color = color_map,labels=label_dic, with_labels = True,pos=pos, node_shape='s')
        
        
        plt.show()
       
            