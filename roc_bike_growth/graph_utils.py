import osmnx as ox
import networkx as nx
from typing import List, Dict

def get_intersections(
    G: nx.MultiDiGraph,
    street_1_name: str,
    street_2_name: str) -> List[int]:
    '''
    Identifies nodes in G that have edges of both street_1_name and street_2_name. 
    
    Parameters
    -------
    G: MultiDiGraph
        Graph of network
    street_1_name: string
        Street of interest, without abbreviations. Capitalization will be ignored. E.x. 'Broad Street'. 
    street_2_name: string
        Street name for intersection. Same naming conventions as `street_1_name`. 
        
        
    Returns
    -------
    nodes: Set
        set of nodes where edges with name `street_1_name` intersect with edges with name `street_2_name`. 
    '''
    street_1_name = street_1_name.lower()
    street_2_name = street_2_name.lower()
    
    # Get all edges for street_name_1
    street_1_edges = {}
    street_1_nodes = []
    for u,v in G.edges():
        d = G.get_edge_data(u,v,0)
        edge_name = d.get('name', '')
        if isinstance(edge_name, list):
            edge_name = ' '.join(edge_name)
            
        edge_name = edge_name.lower()
        if street_1_name in edge_name:
            street_1_edges[(u,v)] = d
            street_1_nodes += [u,v]
    
    # Remove duplicate nodes
    street_1_nodes = set(street_1_nodes)
    
    # Loop through edges to our street nodes to find edges with intersection street names
    street_2_nodes = []
    for u,v in G.edges(street_1_nodes):
        d = G.get_edge_data(u,v,0)
        edge_name = d.get('name','')
        if isinstance(edge_name, list): # Some street names are lists
            edge_name=' '.join(edge_name)

        edge_name = edge_name.lower()

        # TODO change these to regexes?
        if street_2_name in edge_name:
            street_2_nodes += [u,v] 
        else:
            pass
        
    return street_1_nodes.intersection(set(street_2_nodes))

        
def get_street_segment(
    G: nx.MultiDiGraph, 
    street_name: str, 
    intersection_src_name: str, 
    intersection_dest_name: str) -> list:
    '''
    Gets the directed segements of edges with street_name that are between intersection_1_name
    and intersection_2_name. If multiple nodes are found for the intersections, the longest route
    between any two matching intersections is returned. 
    
    Parameters
    -------
    G: MultiDiGraph
        Graph of network
    street_name: string
        Street of interest, without abbreviations. Capitalization will be ignored.
        E.x. 'Broad Street'. 
    intersection_src_name: string
        Street name for source intersection with. Same naming conventions as `street_name`. 
    intersection_dest_name: str
        Street name for dest intersection with. Same naming conventions as `street_name`. 
        
    Returns
    -------
    nodes: list
        List of nodes along the directed segement. 
    '''
    # TODO -- could refactor this to use get_intersections() for brevity. Current implementation works fine. 
    
    # Clean up names
    street_name = street_name.lower()
    intersection_src_name = intersection_src_name.lower()
    intersection_dest_name = intersection_dest_name.lower()
    
    # Get all edges for street_name
    street_edges = {}
    street_nodes = []
    for u,v in G.edges():
        d = G.get_edge_data(u,v,0)
        edge_name = d.get('name', '')
        if isinstance(edge_name, list):
            edge_name = ' '.join(edge_name)
            
        edge_name = edge_name.lower()
        if street_name in edge_name:
            street_edges[(u,v)] = d
            street_nodes += [u,v]
    
    # Remove duplicate nodes
    street_nodes = set(street_nodes)
    
    # Loop through edges to our street nodes to find edges with intersection street names
    src_nodes = []
    dest_nodes = []
    for u,v in G.edges(street_nodes):
        d = G.get_edge_data(u,v,0)
        edge_name = d.get('name','')
        if isinstance(edge_name, list): # Some street names are lists
            edge_name=' '.join(edge_name)

        edge_name = edge_name.lower()

        # TODO change these to regexes?
        if intersection_src_name in edge_name:
            src_nodes += [u,v] 
        elif intersection_dest_name in edge_name:
            dest_nodes += [u,v]
        else:
            pass
    
    src_intersections = street_nodes.intersection(set(src_nodes))
    dest_intersections = street_nodes.intersection(set(dest_nodes))
    
    # Find the longest route between intersections in case there are multiple of either src or dest
    route = []
    for src in src_intersections:
        for dest in dest_intersections:
            # Shortest path of our subgraph will comprise all nodes in between
            new_route = ox.distance.shortest_path(G.subgraph(street_nodes), 
                                              src,
                                              dest)
            # Replace route with longest
            if len(new_route) > len(route):
                route = new_route
    
    return route