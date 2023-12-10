import random

from networkx import DiGraph, relabel_nodes, set_edge_attributes
from numpy import array
from cspy import REFCallback, Tabu, BiDirectional
from loguru import logger


def add_cspy_edge_attributes(data, G):
    """
    Set edge attributes required for cspy
    """
    WALKING_SPEED = 3  # km per hour

    # Initialise edge attributes
    set_edge_attributes(G, 0, 'weight')
    set_edge_attributes(G, 0, 'res_cost')

    # Iterate through edges to specify 'weight' and 'res_cost' attributes
    for edge in G.edges(data=True):
        # Distance is converted from an already existing edge attribute (m to km)
        dist = edge[2]['distance']
        demand = G.nodes[edge[1]]['demand']
        # Fixed resource costs for a given edge.
        cost_edge = 0
        total_delivery = 0
        cost_delivery = 0
        edge[2][('res_cost')] = array([1, dist, demand, total_delivery, cost_edge, cost_delivery])
        edge[2]['weight'] = 0
        # round(1000 * random.random(),0)
    return G


def graph_preparation(data, M):
    R = ['sight','distance', 'demand', 'cost_edge', 'total_delivery', 'cost_delivery']
    # Convert MultiGraph into a Digraph with attribute 'n_res'
    G = DiGraph(M, directed=True, n_res=len(R))
    # Relabel source node to "Source" and sink node to "Sink" (see function for more details)
    G = relabel_nodes(G, {0: 'Source', data.NN +1: 'Sink'})
    # Add res_cost and other resource attributes (see function for more details)
    G = add_cspy_edge_attributes(data, G)
    n_edges = len(G.edges())  # number of edges in network
    print(n_edges)

    return G


class MyCallback(REFCallback):

    def __init__(self):
        REFCallback.__init__(self)
        # Empty attribute for later
        self.G = None

    def REF_fwd(self, cumul_res, tail, head, edge_res, partial_path,
                cumul_cost):
        new_res = list(cumul_res)
        i, j = tail, head
        # distance resource
        new_res[0] += 1
        # distance resource
        new_res[1] += self.G.edges[i,j]['distance']
        # Update 'demand' resource
        new_res[2] += self.G.nodes[j]['demand']
        # # Update 'cost_edge' resource
        new_res[3] += self.G.edges[i, j]['res_cost'][3]
        # Extract the 'total_delivery' resource
        new_res[4] += self.G.edges[i, j]['res_cost'][4]
        # # Update 'cost_delivery' resource
        new_res[5] += self.G.edges[i,j]['res_cost'][5]
        print(f"The current cost in fwd {cumul_cost}")

        return new_res, cumul_cost + 1


def run_labeling_alg(data, dis, All_seq, nodes2keep, nodes2avoid, Duals, R):
    G = graph_preparation(data, data.G)
    # Recall
    #    R = ['sight', 'distance', 'demand', 'total_delivery', 'cost_edge','cost_delivery']
    max_res = [len(G.nodes()), data.Maxtour, data.total_demand, data.C, 100, 100]
    min_res = [0, 0, 0, 0, -100, -100]

    my_callback = MyCallback()

    alg1 = BiDirectional(G, max_res, min_res, REF_callback=my_callback, direction="forward", elementary=True)
    # Pass preprocessed graph
    my_callback.G = alg1.G

    alg1.run()

    logger.debug("Labeling algorithm")
    logger.debug(f"cost = {alg1.total_cost}")
    logger.debug(f"resources = {alg1.consumed_resources}")

