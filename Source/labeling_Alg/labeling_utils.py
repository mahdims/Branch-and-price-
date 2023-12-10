from numpy import array
from numpy.random import RandomState
from networkx import relabel_nodes, set_edge_attributes

WALKING_SPEED = 3  # km per hour


def relabel_source_sink(G,
                        nodes_to_relabel={
                            "Source": "Ternatestraat",
                            "Sink": "Delftweg"
                        }):
    """
    Identify and relabel source and sink nodes.

    Parameters
    ----------
    G : networkx.DiGraph,
        Network to relabel

    nodes_to_relabel : dict,
        Desired nodes to relabel, in the form:
        {"Source": my_source_node, "Sink": my_sink_node}
    """
    # Identify Source and Sink according to specifications
    # Source is the post office in Ternatestraat
    source = [
        e for e in G.edges(data=True)
        if 'name' in e[2] and nodes_to_relabel["Source"] in e[2]['name']
    ][-2][0]
    # Sink is Jane's home in Ceramstraat
    sink = [
        e for e in G.edges(data=True)
        if 'name' in e[2] and nodes_to_relabel["Sink"] in e[2]['name']
    ][0][1]
    # Relabel nodes
    G = relabel_nodes(G, {source: 'Source', sink: 'Sink'})
    return G


def add_edge_attributes(data, duals,G):
    """
    Set edge attributes required for cspy
    """

    # Initialise edge attributes
    set_edge_attributes(G, 0, 'weight')
    set_edge_attributes(G, 0, 'res_cost')
    # 'shift' is not required.
    res_cost_shift = 0

    # Iterate through edges to specify 'weight' and 'res_cost' attributes
    for edge in G.edges(data=True):
        # Distance is converted from an already existing edge attribute (m to km)
        dist = edge[2]['length'] * 0.001
        # Fixed resource costs for a given edge.
        # 'sights' is a random integer between [0, 5)
        res_cost_sights = random_state.randint(1, 5)
        # 'travel-time' is distance over speed (not necessary)
        res_cost_travel_time = dist / float(WALKING_SPEED)
        # 'delivery time' is a random number between the travel-time for
        # the edge and 10 times the travel time.
        # in reality this would depend on the buildings present
        res_cost_delivery_time = random_state.uniform(res_cost_travel_time,
                                                      10 * res_cost_travel_time)
        edge[2]['res_cost'] = array([
            0, res_cost_sights, res_cost_shift, res_cost_travel_time,
            res_cost_delivery_time
        ])
        edge[2]['weight'] = 0  #-dist
    return G