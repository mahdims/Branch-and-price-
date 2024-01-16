from networkx import DiGraph, relabel_nodes, set_edge_attributes
from numpy import array
from cspy import REFCallback, Tabu, BiDirectional
from loguru import logger

def add_edge_attributes(data, duals, G):
    """
    Set edge attributes required for cspy
    """
    # Initialise edge attributes
    set_edge_attributes(G, 0, 'weight')
    set_edge_attributes(G, 0, 'res_cost')

    # Iterate through edges to specify 'weight' and 'res_cost' attributes
    for edge in G.edges(data=True):
        head = edge[1]
        # Distance is converted from an already existing edge attribute (m to km)
        dist = edge[2]['distance']
        demand = G.nodes[head]['demand']
        # Fixed resource costs for a given edge.
        cost_edge =-1 * ((duals[2] - data.Gamma/data.R) * edge[2]['distance'] + (duals[3][head-1] if head != 'Sink' else 0))
        cost_delivery = 0
        edge[2][('res_cost')] = array([1, dist, demand, cost_edge, cost_delivery])
        edge[2]['weight'] = 0
        # This attribute is not dirctly used by the algorithm but is useful for label calculation
        edge[2]['delivery_cost'] = (duals[5] + 1) + (sum((duals[1][head-1, n-1] - duals[1][n-1, head-1]) * G.nodes[n]['demand'] for n in list(G.nodes)[1:-1]) if head != 'Sink' else 0)
    return G


def graph_preparation(data, duals):
    R = ['sight','distance', 'demand', 'cost_edge', 'cost_delivery']
    # Convert MultiGraph into a Digraph with attribute 'n_res'
    G = DiGraph(data.G, directed=True, n_res=len(R))
    # Relabel source node to "Source" and sink node to "Sink" (see function for more details)
    G = relabel_nodes(G, {0: 'Source', data.NN +1: 'Sink'})
    for n in G.nodes:
        if (n, 'Source') in G.edges(): G.remove_edge(n, 'Source')
        if ('Sink', n) in G.edges(): G.remove_edge('Sink', n)

    # Add res_cost and other resource attributes (see function for more details)
    G = add_edge_attributes(data, duals, G)
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
        # Extract the 'delivery_cost' resource
        new_res[4] += self.G.edges[i, j]['res_cost'][4]
        print(f"The current cost in fwd {cumul_cost}")

        return new_res, cumul_cost + 1


def run_labeling_alg(data, dis, All_seq, nodes2keep, nodes2avoid, Duals, R):
    G = graph_preparation(data, Duals)
    # Recall
    #    R = ['sight', 'distance', 'demand', 'total_delivery', 'cost_edge','cost_delivery']
    max_res = [len(G.nodes()), data.Maxtour, data.total_demand, 10, 10]
    min_res = [0, 0, 0, -100, -100]

    my_callback = MyCallback()

    alg1 = BiDirectional(G, max_res, min_res, REF_callback=my_callback, direction="forward", elementary=True)
    # Pass preprocessed graph
    my_callback.G = alg1.G

    alg1.run()

    logger.debug("Labeling algorithm")
    logger.debug(f"cost = {alg1.total_cost}")
    logger.debug(f"resources = {alg1.consumed_resources}")

