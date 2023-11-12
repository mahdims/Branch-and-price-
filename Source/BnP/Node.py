"""
@author: Mahdi Mostajabdaveh
@Email: Mahdi.ms86@gmail.com
@Github: github.com/mahdims
"""

from time import time
import copy
import sys
import heapq
import networkx as nx
import matplotlib.pyplot as plt
from BnP.Master_int import Solve_IMP
from Initial_Alg import Alg
from Column_Gen import ColumnGeneration as CG
from Column_Gen import Master, Sub_model
from utils import Obj_Calc
from BnP import Master_int, Cuts
from utils import utils, Seq


class Node:
    best_Route = []
    best_RDP = []
    UpperBound = float("Inf")
    LowerBound = 0
    Total_time = float("Inf")
    abs_Gini = float("Inf")
    time2UB = - 10
    Data = None
    R = None
    MaxTime = 0
    infeasible_master = False
    Node_dic = {0: []}
    Node_dic2 = {}
    NodeCount = 0
    Tree = nx.Graph()
    
    def __init__(self, ID,  PID, level, pos, Col_dic, G, nodes2keep={}, nodes2avoid={}, cuts=[], Initial_RDP=None):
        
        self.level = level
        self.ID = ID
        self.Parent_ID = PID
        self.pos = pos
        self.Col_dic = Col_dic
        self.G = copy.deepcopy(G)
        self.nodes2keep = nodes2keep
        self.nodes2avoid = nodes2avoid
        self.lower_bound = 0
        self.selected_R_D = []
        self.selected_route = []
        self.Dis = Node.Data.distances
        self.Col_runtime = 0
        self.cuts = cuts
        self.upper_bound, self.Int_route, self.Int_RDP = float("Inf"), [], []
        self.Total_dis = float("Inf")
        self.Gini = float("Inf")
        self.feasible = self.feasibility_check()

        if self.feasible:
            # prepare the seq list
            self.All_seq, self.connected_list, self.feasible = Seq.Create_seq(Node.Data, self.nodes2keep["N"])
            # Add feasible solutions to the Col Dic by initial heuristic
            self.Run_initial_heuristic()
            if not self.feasible and len(self.Col_dic) == 0:
                pass
                # @TODO If the initial alg can't find a feasible solution then run the subproblem to do so, it is unlikly
                # Sub = Sub_model.SubProblem(Node.Data, self.G, self.Dis, self.nodes2keep, self.nodes2avoid)
                # Duals =[]
                # Sub = CG.Set_sub_obj(Node.Data, Node.Data.R, None, Node.dis, Duals, Sub)
            else:
                self.solve()

            if len(self.Col_dic) and (Node.NodeCount % Node.Data.IMP_frequency == 0 or self.ID == 0):
                intObj, IMP_selected_RD, total_time, Gini = \
                    Solve_IMP(Node.Data, Node.R, Node.UpperBound, self.Col_dic)
                if intObj < self.upper_bound and len(IMP_selected_RD) != 0:
                    self.upper_bound = intObj
                    self.Int_route = [self.Col_dic[r] for r, d in IMP_selected_RD]
                    self.Int_RDP = [self.Col_dic[r].RDP[d] for r, d in IMP_selected_RD]
                    self.Total_dis = total_time
                    self.Gini = Gini
                    print(f"At node {self.ID} Integer Master found an UB {intObj}")



        # Extra information (Save the nodes and complete the tree fro drawings)
        Node.NodeCount += 1
        '''        
        Node.Node_dic2[self.ID] = self
        if level < len (Node.Node_dic):
            Node.Node_dic[level].append(self)
        else:
            Node.Node_dic[level]=[self]
        '''
        Node.Tree.add_node(self.ID)
        Node.Tree.add_edge(self.Parent_ID, self.ID)

    def __repr__(self):
        return f"Node {self.ID}: LB: {round(self.lower_bound,2)} UB: {round(self.upper_bound, 2)}"

    def __lt__(self, other):
        return self.lower_bound < other.lower_bound

    def Run_initial_heuristic(self):
        # This function Generates some new R_D according to new dis (edges to avoid)
        NOS = 1 #+ (self.ID == 0)
        F_Sols, F0_sol, self.feasible = Alg.Initial_feasibleSol(Node.Data, self.All_seq,self.Dis, keeps=self.nodes2keep,
                                                        avoids=self.nodes2avoid, number_of_sols=NOS)
        new_routes = []
        if self.feasible:
            for sol in F_Sols:
                if sol.obj < self.upper_bound:
                    self.upper_bound = sol.obj
                    self.Int_route = sol.routes
                    self.Int_RDP = [r.RDP[1] for r in sol.routes]
                    self.Total_dis = sol.total_time
                    self.Gini = sol.q_obj
                new_routes += sol.routes
        else:
            print("Initial heuristic says Infeasible")

        if F0_sol != 0:
            if F0_sol.obj < self.upper_bound:
                self.upper_bound = F0_sol.obj
                self.Int_route = F0_sol.routes
                self.Int_RDP = [r.RDP[1] for r in F0_sol.routes]
                self.Total_dis = F0_sol.total_time
                self.Gini = F0_sol.q_obj
                # new_routes += F0_sol.routes

        # Add the newly generated columns to the Col_dic

        for R_D in new_routes:
            if 0 in R_D.nodes_in_path:
                sys.exit("0 in the route in new cols generated by initial heuristics")
            unique, inx = R_D.Is_unique(self.Col_dic)
            if unique == 1:
                self.Col_dic[inx] = copy.copy(R_D)
            elif unique == 2:
                self.Col_dic[inx].add_RDP(R_D.RDP[1])
            elif unique == 3:
                pass


        # Test
        #out = open("columns", "wb")
        #pk.dump(self.Col_dic, out)
        #out.close()
        #out = open("columns", "rb")
        #self.Col_dic = pk.load(out)
        #out.close()


    def solve(self):
        # This function solves a node (integer relaxation) by column generation
        # Build the master problem
        RMP = Master.MasterModel(Node.Data, self.Col_dic, Node.R)
        # Build the sub-problem only the constraints and variables 
        Sub = Sub_model.SubProblem(Node.Data, self.G, self.Dis, self.nodes2keep["E"], self.nodes2avoid["E"])
        # Add cuts from previous node in BnP tree
        # RMP = Cuts.update_master_subrow_cuts(RMP, self.Col_dic, len(self.cuts), self.cuts)
        # Sub = Cuts.update_subproblem_with_cuts(Sub, len(self.cuts), self.cuts)
        # Start the Column Generation
        start = time()
        while 1:
            self.feasible, RMP, self.lower_bound, self.Y, self.Col_dic = CG.ColumnGen(Node.Data, Node.MaxTime,self.All_seq, Node.R, RMP, self.G, self.Col_dic,
                                                                           self.Dis, self.nodes2keep["E"], self.nodes2avoid["E"], Sub, self.cuts)
            if len(self.Y) == 0:
                Node.infeasible_master = True
            # TEST
            # utils.check_branching(Node.Data, self.Col_dic, self.nodes2avoid["E"], self.nodes2keep["E"])
            #for key, col in self.Col_dic.items():
            #    utils.demand_proportional(Node.Data, col)
            #END TEST
            if not self.feasible:
                break
            print(f"Current lowerbound in Node {self.ID}: {self.lower_bound}")
            break
            # Add cuts
            # new_subrow_cuts = []
            # new_subrow_cuts = Cuts.separation_subrow(Node.Data, self.Col_dic, self.Y, self.cuts)
            #self.cuts += new_subrow_cuts
            # if len(new_subrow_cuts):
            #    print(f"Number of cuts added : {len(new_subrow_cuts)}")
            #    RMP = Cuts.update_master_subrow_cuts(RMP, self.Col_dic, len(self.cuts), new_subrow_cuts)
            #    Sub = Cuts.update_subproblem_with_cuts(Sub, len(self.cuts), new_subrow_cuts)
            #else:
            #    break

        self.Col_runtime = time()-start
        if self.feasible:
            self.selected_R_D = [a for a in self.Y.keys() if self.Y[a] != 0]

    def Strong_Branching(self):
        # Find the branching rule
        Edge_Val = {}
        # calculate the xij values ***** Not for   NN+1 and 0 ******
        for i, j in Node.Data.Gc.edges():
            Edge_Val[(i, j)] = abs(sum([(self.Col_dic[Col_ID].is_visit(i) != -1) * (self.Col_dic[Col_ID].is_visit(j) != -1) * self.Y[Col_ID, RDP_ID]
                                      for Col_ID, RDP_ID in self.selected_R_D]) - 0.5)

        # find the one with the minimum
        
        while 1:
            if len(Edge_Val) == 0:
                # we can not branch this node any further
                return []
            selected_edge = min(Edge_Val, key=Edge_Val.get)
            if selected_edge in self.nodes2avoid["E"] or selected_edge[::-1] in self.nodes2avoid["E"]:
                del Edge_Val[selected_edge]
            elif selected_edge in self.nodes2keep["E"] or selected_edge[::-1] in self.nodes2keep["E"]:
                del Edge_Val[selected_edge]
            else:
                break

        counter = 0
        for key, val in Edge_Val.items():
            if val <= 1.1 * Edge_Val[selected_edge]:
                counter += 1
        print("I select the branching edges among %d alternative randomly!!" %counter)
        L_Node = self.Arc_Branching("left", *selected_edge)
        R_Node = self.Arc_Branching("right", *selected_edge)
        
        return [L_Node, R_Node]
        
    def Arc_Branching(self, WhichNode, i, j):
        # This function will branch on given edge and generates 2 child nodes
        
        Col_dic = copy.deepcopy(self.Col_dic)
        G = copy.deepcopy(self.G)
        
        if WhichNode == "left":
            # update the avoid edges
            nodes2avoid = copy.deepcopy(self.nodes2avoid)

            nodes2avoid, _ = update_avoid_keep(nodes2avoid, self.nodes2keep, i, j, key="avoid")

            # update the set columns by removing routes that i-j or j-i
            for inx, R_D in self.Col_dic.items():
                i_inx = R_D.is_visit(i)
                j_inx = R_D.is_visit(j)

                if i_inx != -1 and j_inx != -1:
                    if (i_inx+1) == j_inx or (j_inx+1) == i_inx:
                        del Col_dic[inx]
                else:
                    pass

            return Node(Node.NodeCount, self.ID, self.level+1, WhichNode, Col_dic, G,
                        cuts=self.cuts, nodes2avoid=nodes2avoid, nodes2keep=self.nodes2keep)

        elif WhichNode == "right":

            # update the keep edges
            nodes2keep = copy.deepcopy(self.nodes2keep)
            nodes2avoid = copy.deepcopy(self.nodes2avoid)
            nodes2avoid, nodes2keep = update_avoid_keep(nodes2avoid, nodes2keep, i, j, key="keep")

            new_cols = {}  # keep the RD that have i-j or j-i Ot neither of them

            for inx, R_D in Col_dic.items():
                i_inx = R_D.is_visit(i)
                j_inx = R_D.is_visit(j)
                if i_inx != -1 and j_inx != -1:
                    if (i_inx+1) == j_inx or (j_inx+1) == i_inx:
                        new_cols[inx] = R_D
                elif i_inx == -1 and j_inx == -1:
                    # If the route do not have both i and j
                    new_cols[inx] = R_D
                else:
                    pass

            Col_dic = new_cols

            return Node(Node.NodeCount, self.ID, self.level+1, WhichNode, Col_dic, G,
                        cuts=self.cuts, nodes2avoid=nodes2avoid, nodes2keep=nodes2keep)

    def rounding(self):
        # @TODO this is not complete and not working!
        selected_col = [(a, self.Y[a]) for a in self.Y.keys() if round(self.Y[a], 4) != 0]
        selected = []
        common_route ={}
        for node in Node.Data.Gc.nodes:
            common_route[node] = []
            for a, val in selected_col:
                if node in self.Col_dic[a[0]].RDP[a[1]]:
                    common_route[node].append((a, val))

    def feasibility_check(self):
        # This function checks if the keep and avoid can make the a node infeasible
        for edge in self.nodes2keep["E"]:
            if edge in self.nodes2avoid["E"] or edge[::-1] in self.nodes2avoid:
                return 0
        # Each keep node should have one or two nodes otherwise
        for key, val in self.nodes2keep["N"].items():
            if len(val) >= 3:
                return 0

        for key, val in self.nodes2keep["N"].items():
            if key in self.nodes2avoid["N"].keys():
                for node in val:
                    if node in self.nodes2avoid["N"][key]:
                        return 0

        return 1

    def integer(self):
        # This function checks if all master problem variables are integer or not
        if self.feasible:
            indictor = all([abs(self.Y[i] - round(self.Y[i],0)) < 0.00001 for i in self.Y.keys()])
        else:
            indictor = False

        if indictor:
            self.upper_bound = self.lower_bound
            self.Int_route = [self.Col_dic[i] for (i, j), val in self.Y.items() if val > 0.9]
            self.Int_RDP = [self.Col_dic[i].RDP[j] for (i, j), val in self.Y.items() if val > 0.9]
            self.Total_dis = sum(route.travel_time for route in self.Int_route)
            self.Gini = utils.calculate_the_obj(Node.Data, self.Int_route, self.Int_RDP)

        return indictor
    
    def delete(self):
        del self.G
        del self

    @classmethod
    def LB_UB_GAP_update(cls, stack, node, start):
        smallest = heapq.nsmallest(1,stack)[0]
        # if Node.LowerBound < smallest.lower_bound:
        Node.LowerBound = smallest.lower_bound

        if node.upper_bound < Node.UpperBound:
            Node.UpperBound = node.upper_bound
            Node.time2UB = round(time() - start, 3)
            if node.integer():
                for (r, id), val in node.Y.items():
                    if val > 0.99:
                        Node.best_Route.append(node.Col_dic[r])
                        Node.best_RDP.append(node.Col_dic[r].RDP[id])
            else:
                Node.best_Route = node.Int_route
                Node.best_RDP = node.Int_RDP
            Node.Total_time = node.Total_dis
            Node.abs_Gini = node.Gini

        Node.Gap = round((Node.UpperBound-Node.LowerBound)*100/Node.UpperBound, 3)

    @classmethod
    def reset(cls):
        Node.best_Route = []
        Node.best_RDP = []
        Node.UpperBound = float("Inf")
        Node.LowerBound = 0
        Node.time2UB = - 10
        Node.Data = None
        Node.R = None
        Node.Node_dic = {0: []}
        Node.Node_dic2 = {}
        Node.NodeCount = 0
        Node.Tree = nx.Graph()
        Node.Total_time = float("Inf")
        Node.abs_Gini = float("Inf")
        Node.infeasible_master = False

    @classmethod
    def Draw_the_tree(cls):
        # @ TODO this function is not in use
        # This function draws the Branch and bound tree 
        W = 100
        label_dic = {} # lable dictionery
        pos = {} # node position dictionery
        x = {0: W/2}
        y = {}
        color_map = []
        maxlevel = len(Node.Node_dic)
        Ystep = W/maxlevel
        for le in range(maxlevel):
            NfNodes = len(Node.Node_dic[le])
            Xstep = W/4*NfNodes
            Node.Node_dic[le] = sorted(Node.Node_dic[le], key=lambda x: x.Parent_ID)
            for inx,n in enumerate(Node.Node_dic[le]):
    
                if n.pos == "left":
                    x[n.ID] = x[Node.Node_dic2[n.Parent_ID].ID] - Xstep
                elif n.pos == "right":
                    x[n.ID] = x[Node.Node_dic2[n.Parent_ID].ID] + Xstep
                else:
                    x[n.ID] = x[Node.Node_dic2[n.Parent_ID].ID]
              
                y[n.ID] = 100 - Ystep * n.level
                pos[n.ID] = (x[n.ID], y[n.ID])
                if not n.feasible:
                    label_dic[n.ID] = "IF-%d " % n.ID
                elif n.integer():
                    label_dic[n.ID] = "IN-%d \n %s" % (n.ID, round(n.lower_bound, 1))
                else:
                    label_dic[n.ID] = "%d-%d" % (n.ID, round(n.lower_bound, 1))

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


def add_a_pair_to_dict(dic, i, j):

    if i != j:
        if (i,j) not in dic["E"] and (j,i) not in dic["E"]:
            dic["E"].append((i, j))

        for n1, n2 in [(i, j), (j, i)]:
            if n1 in dic["N"].keys():
                if n2 not in dic["N"][n1]:
                    dic["N"][n1].append(n2)
            else:
                dic["N"][n1] = [n2]

    return dic


def update_avoid_keep_new_branching(avoid, keep, i, j, key):
    # This function manage the implied branching
    if key == "avoid":

        for k in keep["N"].get(i, []):
            avoid = add_a_pair_to_dict(avoid, j, k)
        for k in keep["N"].get(j, []):
            avoid = add_a_pair_to_dict(avoid, i, k)

        avoid = add_a_pair_to_dict(avoid, i, j)

    elif key == "keep":

        for k in keep["N"].get(j, []):
            keep = add_a_pair_to_dict(keep, i, k)

        for k in keep["N"].get(i, []):
            keep = add_a_pair_to_dict(keep, j, k)
            for h in keep["N"].get(j, []):
                keep = add_a_pair_to_dict(keep, h, k)

        for k in avoid["N"].get(i, []):
            avoid = add_a_pair_to_dict(avoid, j, k)
        for k in avoid["N"].get(j, []):
            avoid = add_a_pair_to_dict(avoid, i, k)

        keep = add_a_pair_to_dict(keep, i, j)

    return avoid, keep


def update_avoid_keep(avoid, keep, i, j, key):
    # This function manage the implied branching
    if key == "avoid":

        avoid = add_a_pair_to_dict(avoid, i, j)

    elif key == "keep":

        keep = add_a_pair_to_dict(keep, i, j)

    return avoid, keep