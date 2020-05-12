
from Node import Node
from feasibleSol import Initial_feasibleSol 
from Real_Input import Real_Input
import cPickle as Pick
import time

def read_object(filename):
    with open(filename, 'rb') as input:
        obj= Pick.load(input)
    return  obj
    
def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        Pick.dump(obj, output, Pick.HIGHEST_PROTOCOL)
        
        
def branch_and_bound(Data,R,MaxTime):
    
    start= time.time()
    Node.Data=Data
    Node.R=R
    # set initial parameters
    Node.best_obj = 100000000000000000 # upper bound 
    Node.best_objtime=0
    Gap=100
    Elapsed_time=0
    # initiate the algorithm
    Col_set , _ = Initial_feasibleSol(Data , Data.G ) #find the intial columns
    Col_dic={} # convert them to a dic
    for inx,R_D in enumerate(Col_set):
            Col_dic[inx] = R_D  
    # make the root node
    root = Node(0,0,0, "center" , Col_dic, Data.G)
    Node.LowerBound = round( root.Objval , 2 )
    print("Start the BnP with root value %s"%Node.LowerBound )
    if root.integer() : # check if we need to continue
        Node.best_obj = round(root.Objval,2)
        Node.best_node=root
        Node.best_Route=root.selected_route
        return (Node.best_node, Node.best_obj ,Node.LowerBound ,Node.best_objtime ,Elapsed_time ,Gap)

    # branch and create two fist nodes
    stack = root.Strong_Branching()

    ############# MAin loop #################
    while len(stack)!=0  and  Gap > 0.01 and Elapsed_time <MaxTime:
        node = min(stack, key = lambda i: i.Objval) # select the node with best objval
        stack.remove(node)        
        if not node.feasible:
            node.delete( )
            continue
        Node.LowerBound=round(node.Objval,2) # lower bound is the minmum obj among the un explored ones        
        
         # remove the node form pool of unexplored nodes

        if node.Objval >= Node.best_obj: #Fanthom by infeasiblity or bound
            node.delete( )
            continue
        # check if the node deterime the upper or lowerbound
           
        if node.integer() : # Fanthom by integerity 
            if node.Objval < Node.best_obj: # update upperbound 
                Node.best_obj = round(node.Objval,2)
                Node.best_objtime=round(time.time()-start,3)
                Node.best_node = node
            node.delete( )
            continue
        if node.Int_Objval < Node.best_obj:
             Node.best_obj = round(node.Int_Objval,2)
             Node.best_objtime=round(time.time()-start,3)
             Node.best_Route=node.Int_route
             Node.best_RDP=node.Int_RDP
             
        # select the branching rule
        # generates two child node
        child_nodes =  node.Strong_Branching()
        stack += child_nodes
        
        #Node.Draw_the_tree()
        #print ("Number of block edges : %s" %len(node.edge2avoid))
        #print("Number of most visit edges: %s" %len(node.edges2keep))
        if Node.best_obj:
            Gap=round( (Node.best_obj-Node.LowerBound)*100/Node.best_obj ,3 )
        else:
            Gap=None
        Elapsed_time=round(time.time()-start,3)
        #print("ID // Current objval // integer Objval // UB    // LB     // GAP // Elapsed T")
        print("%d     %s        %s          %s    %s   %s   %s" 
            %(node.ID, round(node.Objval,2), round(node.Int_Objval,2), Node.best_obj, Node.LowerBound ,Gap,Elapsed_time ) )
        node.delete( )
    return (Node.best_node, Node.best_obj ,Node.LowerBound ,Node.best_objtime ,Elapsed_time ,Gap)

''' 
#NN=40 # number of nodes
#M=8 # number of vehicles 
#Q=50 # vehicles Capacity
#C=0.75 # percentage of demand as Initial inventory in depot
#Lambda=0.5 # Gini weight in obj 
#Gamma=0.1 # weight of total travel time function in obj
#Data=Input(NN,M,Q,C,Lambda,Gamma)
#save_object( Data , 'Data.pkl_%d_%d_%d' %(NN,M,Q) )
#Data=read_object('Kartal_3_100_%d' %(NN,M,Q)) # read Data stored in directory 
#Data=read_object('G:\My Drive\\1-PhD thesis\equitable relief routing\Code\Kartal\Kartal_3_100_0') 
Data=read_object('G:\My Drive\\1-PhD thesis\equitable relief routing\Code\Van\Van_15_3_1') 
#Data.Gamma=0
Data.Q=3000
#Data.Maxtour=300

start= time.time()
Bsolution = branch_and_bound(Data)
RunTime_BnB = time.time()-start
if Bsolution:
    print(Bsolution.Objval , RunTime_BnB)
    for i in Bsolution.selected_R_D:
        r= Bsolution.Col_dic[i]
        print(r.route)
        print(r.RDP)
        print("Total delivery in this tour: %s" %sum(r.RDP))
        print("The Tour length is : %s \n" %round(r.travel_time,1) )
else:
    for j,r in  enumerate(Node.best_Route):
        print(r)
        print(Node.best_RDP[j])
        print("Total delivery in this tour: %s" %sum(Node.best_RDP[j]))
        #print("The Tour length is : %s \n" %round(r.travel_time,1) )
    print ("Optimal solution: %s" %Node.best_obj)
'''