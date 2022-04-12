import networkx as nx

def graph_resilience(G, variant = 'density'):
    assert variant in ['density', 'largest_component']
    if variant == 'density':
        return nx.density(G)
    elif variant == 'largest_component':
        G_new = G.to_undirected(as_view=False)
        return len(max(nx.connected_components(G_new), key=len))
        
def cal_n_components(G):
    G_new = G.to_undirected(as_view=False)
    return len(list(nx.connected_components(G_new)))

def graph_cohesion(G, coverage):
    assert isinstance(coverage, float) 
    n_components = cal_n_components(G)
    return coverage / (n_components**2 + 0.00001)

def graph_coverage(G):
    raise NotImplementedError
    return 1.2

def graph_global_efficiency(G):
    return nx.algorithms.efficiency.global_efficiency(G)

def graph_local_efficiency(G):
    return nx.algorithms.efficiency.local_efficiency(G)