import osmnx as ox
import networkx as nx
from typing import List, Dict


def get_intersections(
    G: nx.MultiDiGraph, street_1_name: str, street_2_name: str
) -> List[int]:
    """
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
    """
    street_1_name = street_1_name.lower()
    street_2_name = street_2_name.lower()

    # Get all edges for street_name_1
    street_1_edges = {}
    street_1_nodes = []
    for u, v in G.edges():
        d = G.get_edge_data(u, v, 0)
        edge_name = d.get("name", "")
        if isinstance(edge_name, list):
            edge_name = " ".join(edge_name)

        edge_name = edge_name.lower()
        if street_1_name in edge_name:
            street_1_edges[(u, v)] = d
            street_1_nodes += [u, v]

    # Remove duplicate nodes
    street_1_nodes = set(street_1_nodes)

    # Loop through edges to our street nodes to find edges with intersection street names
    street_2_nodes = []
    for u, v in G.edges(street_1_nodes):
        d = G.get_edge_data(u, v, 0)
        edge_name = d.get("name", "")
        if isinstance(edge_name, list):  # Some street names are lists
            edge_name = " ".join(edge_name)

        edge_name = edge_name.lower()

        # TODO change these to regexes?
        if street_2_name in edge_name:
            street_2_nodes += [u, v]
        else:
            pass

    return street_1_nodes.intersection(set(street_2_nodes))


def get_street_segment(
    G: nx.MultiDiGraph,
    street_name: str,
    intersection_src_name: str,
    intersection_dest_name: str,
) -> list:
    """
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
    """
    # TODO -- could refactor this to use get_intersections() for brevity. Current implementation works fine.

    # Clean up names
    street_name = street_name.lower()
    intersection_src_name = intersection_src_name.lower()
    intersection_dest_name = intersection_dest_name.lower()

    # Get all edges for street_name
    street_edges = {}
    street_nodes = []
    for u, v in G.edges():
        d = G.get_edge_data(u, v, 0)
        edge_name = d.get("name", "")
        if isinstance(edge_name, list):
            edge_name = " ".join(edge_name)

        edge_name = edge_name.lower()
        if street_name in edge_name:
            street_edges[(u, v)] = d
            street_nodes += [u, v]

    # Remove duplicate nodes
    street_nodes = set(street_nodes)

    # Loop through edges to our street nodes to find edges with intersection street names
    src_nodes = []
    dest_nodes = []
    for u, v in G.edges(street_nodes):
        d = G.get_edge_data(u, v, 0)
        edge_name = d.get("name", "")
        if isinstance(edge_name, list):  # Some street names are lists
            edge_name = " ".join(edge_name)

        edge_name = edge_name.lower()

        # TODO change these to regexes?
        if intersection_src_name in edge_name:
            src_nodes += [u, v]
        elif intersection_dest_name in edge_name:
            dest_nodes += [u, v]
        else:
            pass

    src_intersections = street_nodes.intersection(set(src_nodes))
    dest_intersections = street_nodes.intersection(set(dest_nodes))

    # Find the longest route between intersections in case there are multiple of either src or dest
    route = []
    for src in src_intersections:
        for dest in dest_intersections:
            # Shortest path of our subgraph will comprise all nodes in between
            new_route = ox.distance.shortest_path(G.subgraph(street_nodes), src, dest)
            # Replace route with longest
            if len(new_route) > len(route):
                route = new_route

    return route

def combine_nodes(    
    dst: nx.MultiDiGraph, 
    src: nx.MultiDiGraph, 
    node_attributes = ['x','y','street_count'], 
    debug = False):
    
    
    ''' 
    Adds the nodes from one graph to another.
    
    Parameters   
    ------
    dst: MultiDiGraph
        Graph of network that edges are being added to
    src: MultiDiGraph
        Graph of network whose edges are added to dst 
        
    Returns
    ------
    
    dst: 
        Graph dst with added edges from src
    '''
    
    # Get the keys for the nodes in both graphs 
    
    dst_nodes = list(dict(dst.nodes(data=True)).keys())
    src_nodes = list(dict(src.nodes(data=True)).keys())
    
    # Add the nodes from src not in dst to dst 
    
    for node in src_nodes:
        if(node in dst_nodes):
            pass
        else:
            dst.add_node(node)
            for a in node_attributes:
                #set attributes
                dst.nodes[node][a] = src.nodes[node][a]
    return dst

def combine_edges(
    dst: nx.MultiDiGraph, 
    src: nx.MultiDiGraph, 
    debug = False):
    
    ''' 
    Adds the edges from one graph to another 
    (assuming they have the edges only contain nodes that are in the dst graph)
    
    Parameters   
    ------
    dst: MultiDiGraph
        Graph of network that edges are being added to
    src: MultiDiGraph
        Graph of network whose edges are added to dst 
        
    Returns
    ------
    
    dst: 
        Graph dst with added edges from src
    '''
    
    
    # Get the keys for the values between edges (would need to use multiple edges 
    
    src_edges = list(src.edges)
    dst_edges = list(dst.edges)
    
    # Add edges not in dst to dst from src 

    for edge in src_edges:
        if(edge in dst_edges):
            pass
        else:
            attr = dict(src[edge[0]][edge[1]][edge[2]])
            dst.add_edge(edge[0],edge[1])
            edge_attr = {edge: attr}
            if(debug):
                print(edge_a)
            nx.set_edge_attributes(dst,edge_attr)
    return dst

def ig_to_nx(
    G_ig: igraph.Graph
    ):
    
    #Inits empty networkx MultiDiGraph
    
    G_nx = nx.MultiDiGraph()
    
    for node in G_ig.vs:
        #The networkx key values are called _nx_name in iGraph 
        
        key = node['_nx_name']
        
        #adds the node attributes of the iGraph node to new node in nx at key of node
        
        G_nx.add_node(key)
        a = node.attributes()
        del a['_nx_name']
        attrs = {key: a}
        
        nx.set_node_attributes(G_nx, attrs)
        
    for edge in G_ig.es:
        
        #Get the keys of the edge in terms of nx keys
        
        src_i = edge.source
        trg_i = edge.target
        src = G_ig.vs[src_i]['_nx_name']
        trg = G_ig.vs[trg_i]['_nx_name']
        
        #add the edges to the nx graph with attributes

        G_nx.add_edge(src, trg)
        a = edge.attributes()
        attrs = {(src,trg,0 ): a}
        
        nx.set_edge_attributes(G_nx,attrs)

    #Sets the graph attributes
    
    for a in G_ig.attributes():
        
        G_nx.graph[a] = G_ig[a]
    
    return G_nx
