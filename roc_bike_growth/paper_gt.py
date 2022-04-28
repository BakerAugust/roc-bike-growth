import networkx as nx
import osmnx as ox
import random
import copy
import igraph as ig
import numpy as np
import math
import random
import time
import pickle as pk
import roc_bike_growth.graph_utils as gu

# Algorithm the same as the one in their code with some unnessecary bits  removed.
# Enumerates all of the connections between points of interest in graph and sums over their weights
def get_poipairs_by_distance(G, pois_indices, route_factor = 0):
    # Get sequences of nodes and edges in shortest paths between all pairs of pois
    poi_nodes = []
    poi_edges = []
    
    if(True):
        for e in G.es:
            e["mod_weight"] = e["weight"] - e["weight"] * route_factor * int(
                e["existing"] == True
            )
            
        
    
    for c, v in enumerate(pois_indices):
        # Possible cost parameters we could add to weight could be calculated here.
        # We'd have to implement a "get shortest paths  weighted on accident data etc."
        # could also include node weights
        poi_nodes.append(G.get_shortest_paths(v, pois_indices[c:], output="vpath", weights = "mod_weight"))
        poi_edges.append(G.get_shortest_paths(v, pois_indices[c:], output="epath", weights = "mod_weight"))
    
    

    # Sum up weights (distances) of all paths
    poi_dist = {}
    for paths_n, paths_e in zip(poi_nodes, poi_edges):
        for path_n, path_e in zip(paths_n, paths_e):
            # Sum up distances of path segments from first to last node
            # would have to use distances incorporating parameters if we were to use them here.
            path_dist = sum([G.es[e]["mod_weight"] for e in path_e])
            if path_dist > 0:
                poi_dist[(path_n[0], path_n[-1])] = path_dist

    temp = sorted(poi_dist.items(), key=lambda x: x[1])
    # Back to ids
    poipairs = []
    for p in temp:
        poipairs.append([(G.vs[p[0][0]]["id"], G.vs[p[0][1]]["id"]), p[1]])

    return poipairs


def greedy_triangulation(GT, poipairs, prune_factor=1, route_factor = 0, prune_measure="betweenness"):
    for poipair, poipair_distance in poipairs:
        try:
            poipair_ind = (
                GT.vs.find(id=poipair[0]).index,
                GT.vs.find(id=poipair[1]).index,
            )
        except:
            print(poipair)
            for v in GT.vs:
                print(v["id"])

        if not new_edge_intersects(
            GT,
            (
                GT.vs[poipair_ind[0]]["x"],
                GT.vs[poipair_ind[0]]["y"],
                GT.vs[poipair_ind[1]]["x"],
                GT.vs[poipair_ind[1]]["y"],
            ),
        ):
            GT.add_edge(poipair_ind[0], poipair_ind[1], weight=poipair_distance)

    # Get the measure for pruning
    
    print(prune_measure)
    
    prune_quantile = prune_factor
    
    if prune_measure == "betweenness" or prune_measure == "hybrid":
        BW = GT.edge_betweenness(directed = True, weights = "weight")
        qt = np.quantile(BW, 1-prune_quantile)
        sub_edges = []
        for c, e in enumerate(GT.es):
            if BW[c] >= qt: 
                sub_edges.append(c)
            GT.es[c]["bw"] = BW[c]
            GT.es[c]["width"] = math.sqrt(BW[c]+1)*0.5
        # Prune
        GT = GT.subgraph_edges(sub_edges)
    elif prune_measure == "closeness":
        CC = GT.closeness(vertices = None, weights = "weight")
        qt = np.quantile(CC, 1-prune_quantile)
        sub_nodes = []
        for c, v in enumerate(GT.vs):
            if CC[c] >= qt: 
                sub_nodes.append(c)
            GT.vs[c]["cc"] = CC[c]
        GT = GT.induced_subgraph(sub_nodes) 
        
    elif prune_measure == "iter_betweenness":
        print('here')
    
    return GT


# Get node pairs we need to route, sorted by distance
# allows us to only includ relevant pairs in
def route_node_pairs(G, GT, route_factor):
    
    for e in G.es:
        e["mod_weight"] = e["weight"] - e["weight"] * route_factor * int(
            e["existing"] == True
        )
    
    routenodepairs = {}
    for e in GT.es:
        routenodepairs[(e.source_vertex["id"], e.target_vertex["id"])] = e["weight"]
    routenodepairs = sorted(routenodepairs.items(), key=lambda x: x[1])

    # Do the routing
    GT_indices = set()


    for poipair, poipair_distance in routenodepairs:
        poipair_ind = (G.vs.find(id=poipair[0]).index, G.vs.find(id=poipair[1]).index)
        sp = set(
            G.get_shortest_paths(
                poipair_ind[0], poipair_ind[1], weights="mod_weight", output="vpath"

            )[0]
        )
        GT_indices = GT_indices.union(sp)

    GT_final = G.induced_subgraph(GT_indices)
    return GT_final


# the below classes are ripped from the code. its an intersection function which could probably be optimized better but it definitely works :)
class MyPoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y


def new_edge_intersects(G, enew):
    """Given a graph G and a potential new edge enew,
    check if enew will intersect any old edge.
    """
    E1 = MyPoint(enew[0], enew[1])
    E2 = MyPoint(enew[2], enew[3])
    for e in G.es():
        O1 = MyPoint(e.source_vertex["x"], e.source_vertex["y"])
        O2 = MyPoint(e.target_vertex["x"], e.target_vertex["y"])
        if segments_intersect(E1, E2, O1, O2):
            return True
    return False


def segments_intersect(A, B, C, D):
    """Check if two line segments intersect (except for colinearity)
    Returns true if line segments AB and CD intersect properly.
    Adapted from: https://stackoverflow.com/questions/3838329/how-can-i-check-if-two-segments-intersect
    """
    if (
        (A.x == C.x and A.y == C.y)
        or (A.x == D.x and A.y == D.y)
        or (B.x == C.x and B.y == C.y)
        or (B.x == D.x and B.y == D.y)
    ):
        return False  # If the segments share an endpoint they do not intersect properly
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


def ccw(A, B, C):
    return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)


# craete a deepcopy of the original graph with no edges


def set_all_edge_attributes(G_src, G_dst, atr_name):
    edges = list(G_src.edges)
    atr = {}
    for edge in edges:
        atr[edge] = True
    nx.set_edge_attributes(G_dst, atr, atr_name)
    return G_dst


# def greedy_triangulation_subgraph(G, pois_indices = [], pois_method = pass):
def gt_from_scratch(G, pois_indices, route_factor=0, prune_factor=1, prune_measure = "betweenness"):
    G_temp = copy.deepcopy(G)
    for e in G_temp.es:  # delete all edges
        G_temp.es.delete(e)
    GT = copy.deepcopy(G_temp.subgraph(set(pois_indices)))
    poipairs = get_poipairs_by_distance(G, pois_indices, route_factor = route_factor)
    # print(poipairs)
    GT = greedy_triangulation(GT, poipairs, prune_factor, prune_measure = prune_measure, route_factor = route_factor)
    GT_final = route_node_pairs(G, GT, route_factor)
    return GT_final


def gt_with_existing_full(G_base, G_existing, route_factor=0, prune_factor=1, prune_measure = "betweenness", by_factor ="mod", distance_limit = 99999999999):

    G_comb_nx = gu.combine_nodes(G_base, G_existing)
    G_comb_nx = gu.combine_edges(G_comb_nx, G_existing)

    G_comb_nx = set_all_edge_attributes(G_existing, G_comb_nx, "existing")

    G_comb = ig.Graph.from_networkx(G_comb_nx)

    for i, v in enumerate(G_comb.vs):
        v["id"] = i
    for e in G_comb.es:
        e["weight"] = e["length"]
    pois_ids = [v_index for v_index, vertex in enumerate(G_comb.vs) if vertex["poi"]]
    G_gen = gt_from_scratch(G_comb, pois_ids, route_factor, prune_factor,prune_measure = prune_measure)
    if((prune_measure == 'iter_betweenness') or (prune_measure == 'hybrid')):
        G_gen = iterative_pruning(G_gen,G_existing, prune_factor, by_factor)
        print('here')
    G_nx = gu.ig_to_nx(G_gen)
    G_nx = gu.combine_nodes(G_nx, G_existing)
    G_nx = gu.combine_edges(G_nx, G_existing)

    G_nx = set_all_edge_attributes(G_existing, G_nx, "existing")
    G_nx = set_all_edge_attributes(gu.ig_to_nx(G_gen), G_nx, "generated")
    
    if(prune_measure == 'iter_betweenness'):
        G_nx.remove_nodes_from(list(nx.isolates(G_nx)))
        
    return G_nx
            
def iterative_pruning(GT, existing, prune_factor, by_factor):
    
    if(by_factor == "mod"):
        #modified by factor speeding up algorithm
        #start = 20, half  = 10, 1/4 =5 1/8 = 2 1/16 = 1
        by_factors = [40,20,10,5,2,1] 
    else:
        by_factors =  [by_factor]*6
    
    edges = len(GT.es) 
    new_edges = edges * prune_factor + len(existing.edges)
    rm_edges = edges - new_edges
    factor = 0.5
    bf_index = 0
    
    while(len(GT.es) > new_edges):
        
        if(((len(GT.es) - new_edges)/rm_edges < factor) & (bf_index !=5)):
            
            factor = factor/2
            bf_index+=1
        print('factor: ' + str(by_factors[bf_index]))
        
        BW = GT.edge_betweenness(directed = True, weights = "mod_weight")
        
        for index,edge in enumerate(GT.es):
            
            if(edge['existing'] == True):
                
                BW[index] = 9999999999
           
        bf_temp  = by_factors[bf_index]        
        min_values = sorted(list(set(BW)))[0:bf_temp]
        edges = []
        
        for min_value in min_values:
            
            pos = list(np.where(np.array(BW) == min_value)[0])
            edges = [GT.es[i] for i in pos] + edges
        
        print(len(edges))
            
        GT.delete_edges(edges)
        
    print(len(GT.es))
    
    return GT
