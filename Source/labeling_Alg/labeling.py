from networkx import DiGraph
from labeling_Alg.labeling_utils import relabel_source_sink, add_cspy_edge_attributes
from numpy import array
from cspy import REFCallback, Tabu, BiDirectional


WALKING_SPEED = 3
def graph_preparation(data, M):

    R = ['mono', 'sights', 'shift', 'travel-time', 'delivery-time']

    # Convert MultiGraph into a Digraph with attribute 'n_res'
    G = DiGraph(M, directed=True, n_res=len(R))
    # Relabel source node to "Source" and sink node to "Sink" (see function for more details)
    G = relabel_source_sink(G)
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
        # Monotone resource
        new_res[0] += 1
        # Update 'sights' resource
        new_res[1] += self.G.edges[i,j]['res_cost'][1]
        # Extract the 'travel-time' resource (distance/speed)
        new_res[3] = - self.G.edges[i,j]['weight'] / float(WALKING_SPEED)
        # # Update 'delivery-time' resource
        new_res[4] = self.G.edges[i,j]['res_cost'][4]
        # # Update 'shift' resource
        new_res[2] += (new_res[3] + new_res[4])  # travel-time + delivery-time
        return new_res


def run_labeling_alg(Data, dis, All_seq, nodes2keep, nodes2avoid, Duals, R):
    G =  graph_preparation(Data.G)
    # Recall
    #     R = ['mono', 'sights', 'shift', 'travel-time', 'delivery-time']
    max_res = [n_edges, 5*n_edges, 5, 5, 5]
    min_res = [0, 0, 0, 0, 0]

    my_callback = MyCallback()

    alg1 = BiDirectional(G, max_res, min_res, REF_callback=my_callback, direction="forward", elementary=True)
    # Pass preprocessed graph
    my_callback.G = alg1.G
    alg1.run()

    print(alg1.path)
    print(alg1.total_cost)
    print(alg1.consumed_resources)

