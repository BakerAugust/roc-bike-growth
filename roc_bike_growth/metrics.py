import networkx as nx
import random
import itertools
import igraph as ig
from haversine import haversine_vector
import pyproj
from shapely import ops
from shapely.geometry import Polygon, LineString
import copy

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

def dist_vector(v1_list, v2_list):
    dist_list = haversine_vector(v1_list, v2_list, unit="m") # [(lat,lon)], [(lat,lon)]
    return dist_list

def graph_global_efficiency(G):
    return nx.algorithms.efficiency.global_efficiency(G)

def graph_local_efficiency(G):
    return nx.algorithms.efficiency.local_efficiency(G)

def paper_global_efficiency(G, pairs_thresh=500):
    # Input is a igraph Graph
    try:
        G = ig.Graph.from_networkx(nx.Graph(G))
    except:
        pass
    
    if G.vcount() > pairs_thresh:
        nodeindices = random.sample(list(G.vs.indices), pairs_thresh)
    else:
        nodeindices = list(G.vs.indices)
    
    d_ij = G.shortest_paths(source = nodeindices, target = nodeindices)
    d_ij = [item for sublist in d_ij for item in sublist] # flatten
    EG  = sum([1/d for d in d_ij if d != 0])
    pairs = list(itertools.permutations(nodeindices, 2))
    l_ij = dist_vector([(G.vs[p[0]]["y"], G.vs[p[0]]["x"]) for p in pairs],
                            [(G.vs[p[1]]["y"], G.vs[p[1]]["x"]) for p in pairs]) # must be in format lat,lon = y,x
    EG_id = sum([1/l for l in l_ij if l != 0])
    
    return EG / EG_id

def paper_local_efficiency(G, numnodepairs=500):
    # Input is a igraph Graph
    try:
        G = ig.Graph.from_networkx(nx.Graph(G))
    except:
        pass
    
    if G.vcount() > numnodepairs:
        nodeindices = random.sample(list(G.vs.indices), numnodepairs)
    else:
        nodeindices = list(G.vs.indices)
    EGi = []
    for i in nodeindices:
        if len(G.neighbors(i)) > 1: # If we have a nontrivial neighborhood
            G_induced = G.induced_subgraph(G.neighbors(i))
            EGi.append(paper_global_efficiency(G_induced, numnodepairs))
    EGi = sum(EGi) / len(EGi)
    
    return EGi

def paper_coverage(G):
    G = ig.Graph.from_networkx(nx.Graph(G))
    G_added = copy.deepcopy(G)
    
    # https://gis.stackexchange.com/questions/121256/creating-a-circle-with-radius-in-metres
    longitudes = [v["x"] for v in G.vs]
    loncenter = sum(longitudes) / (len(longitudes) + 0.0001)
    latitudes = [v["y"] for v in G.vs]
    latcenter = sum(latitudes) / (len(latitudes) + 0.0001)
    local_azimuthal_projection = "+proj=aeqd +R=6371000 +units=m +lat_0={} +lon_0={}".format(latcenter, loncenter)
    
    # Use transformer: https://gis.stackexchange.com/questions/127427/transforming-shapely-polygon-and-multipolygon-objects
    wgs84_to_aeqd = pyproj.Transformer.from_proj(
        pyproj.Proj("+proj=longlat +datum=WGS84 +no_defs"),
        pyproj.Proj(local_azimuthal_projection))
    aeqd_to_wgs84 = pyproj.Transformer.from_proj(
        pyproj.Proj(local_azimuthal_projection),
        pyproj.Proj("+proj=longlat +datum=WGS84 +no_defs"))
    edgetuples = [((e.source_vertex["x"], e.source_vertex["y"]), (e.target_vertex["x"], e.target_vertex["y"])) for e in G_added.es]
    
    # # Shapely buffer seems slow for complex objects: https://stackoverflow.com/questions/57753813/speed-up-shapely-buffer
    # # Therefore we buffer piecewise.
    cov_added = Polygon()
    for c, t in enumerate(edgetuples):
        buf = ops.transform(aeqd_to_wgs84.transform, ops.transform(wgs84_to_aeqd.transform, LineString(t)).buffer(500))
        cov_added = ops.unary_union([cov_added, Polygon(buf)])

    cov_transformed = ops.transform(wgs84_to_aeqd.transform, cov_added)
    covered_area = cov_transformed.area / 1000000 # turn from m2 to km2

    return covered_area