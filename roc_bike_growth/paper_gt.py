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

# Algorithm the same as the one in their code with some unnessecary bits  removed.
# Enumerates all of the connections between points of interest in graph and sums over their weights
def get_poipairs_by_distance(G, pois_indices):
    # Get sequences of nodes and edges in shortest paths between all pairs of pois
    poi_nodes = []
    poi_edges = []
    for c, v in enumerate(pois_indices):
        # Possible cost parameters we could add to weight could be calculated here.
        # We'd have to implement a "get shortest paths  weighted on accident data etc."
        # could also include node weights
        poi_nodes.append(G.get_shortest_paths(v, pois_indices[c:], output="vpath"))
        poi_edges.append(G.get_shortest_paths(v, pois_indices[c:], output="epath"))

    # Sum up weights (distances) of all paths
    poi_dist = {}
    for paths_n, paths_e in zip(poi_nodes, poi_edges):
        for path_n, path_e in zip(paths_n, paths_e):
            # Sum up distances of path segments from first to last node
            # would have to use distances incorporating parameters if we were to use them here.
            path_dist = sum([G.es[e]["weight"] for e in path_e])
            if path_dist > 0:
                poi_dist[(path_n[0], path_n[-1])] = path_dist

    temp = sorted(poi_dist.items(), key=lambda x: x[1])
    # Back to ids
    poipairs = []
    for p in temp:
        poipairs.append([(G.vs[p[0][0]]["id"], G.vs[p[0][1]]["id"]), p[1]])

    return poipairs


def greedy_triangulation(GT, poipairs, prune_factor=1, prune_measure="betweenness"):
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
    # if prune_measure == "betweenness":
    BW = GT.edge_betweenness(directed=False, weights="weight")
    # here is where we can include some other attributes: for instance BW = betweenness/log(accident likelihood)
    qt = np.quantile(BW, 1 - prune_factor)
    sub_edges = []
    for c, e in enumerate(GT.es):
        if BW[c] >= qt:
            sub_edges.append(c)
            # we only keep edge c if it is in the pf percentile of edges in our metric (0 = no edges, 1 = all edges from GT)
        GT.es[c]["bw"] = BW[c]
        GT.es[c]["width"] = math.sqrt(BW[c] + 1) * 0.5
    GT = GT.subgraph_edges(sub_edges)
    return GT


# Get node pairs we need to route, sorted by distance
# allows us to only includ relevant pairs in
def route_node_pairs(G, GT):
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
                poipair_ind[0], poipair_ind[1], weights="weight", output="vpath"
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

# def greedy_triangulation_subgraph(G, pois_indices = [], pois_method = pass):
def gt_from_scratch(G, pois_indices, prune_factor=1):

    G_temp = copy.deepcopy(G)
    for e in G_temp.es:  # delete all edges
        G_temp.es.delete(e)
    GT = copy.deepcopy(G_temp.subgraph(set(pois_indices)))
    poipairs = get_poipairs_by_distance(G, pois_indices)
    # print(poipairs)
    GT = greedy_triangulation(GT, poipairs, prune_factor)
    GT_final = route_node_pairs(G, GT)
    return GT_final
