import osmnx as ox
import networkx as nx

# TODO
# - add tests
# - pull out a separate function for get_intersection(). 

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
    
    # Clean up names
    street_name = street_name.lower()
    intersection_src_name
    intersection_dest_name
    
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
    
    src_intersection = street_nodes.intersection(set(src_nodes))
    dest_intersection = street_nodes.intersection(set(dest_nodes))
    
    # Find the longest route between intersections in case there are multiple
    route = []
    for src in src_intersection:
        for dest in dest_intersection:
            # Shortest path of our subgraph will comprise all nodes in between
            new_route = ox.distance.shortest_path(G.subgraph(street_nodes), 
                                              src,
                                              dest)
            # Replace route with longest
            if len(new_route) > len(route):
                route = new_route
    
    return route