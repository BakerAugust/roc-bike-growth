import osmnx as ox
import networkx as nx
import numpy as np
from roc_bike_growth.settings import CONFIG
from shapely.geometry import Polygon 
from typing import List


def download_POIs(polygon: Polygon, custom_filters: dict = CONFIG.osm_poi_params) -> dict:
    '''
    Queries overpass for nodes in polygon with matching filters and returns json response.
    
    Parameters
    -------
    polygon: Polygon
        Shapely Polygon object to use as query boundary. 
    custom_filters: list
        list of custom filters for the nodes. E.x. '["amenity"="school"]'   
        
    Returns
    -------
    dict
    
    '''
    
    # format overpass query
    overpass_settings = ox.downloader._make_overpass_settings()
    
    # convert polygon to Overpass poly string
    polygon_str = ox.downloader._make_overpass_polygon_coord_strs(polygon)
    
    # Construct filters as strings
    components = []
    for custom_filter in custom_filters.values():
        components.append(f'node{custom_filter}(poly:"{polygon_str[0]}")')
    
    # Do overpass query
    query = f"{overpass_settings};({';'.join(components)};>;);out;"

    return ox.downloader.overpass_request(data={'data':query})
    
    
def POI_graph_from_polygon(polygon: Polygon, custom_filters: dict = CONFIG.osm_poi_params) -> nx.MultiDiGraph:
    '''
    Queries overpass for nodes in polygon with matching filters and returns a graph.
    
    Parameters
    -------
    polygon: Polygon
        Shapely Polygon object to use as query boundary. 
    custom_filters: list
        list of custom filters for the nodes. E.x. '["amenity"="school"]'   
        
    Returns
    -------
    nx.MultiDiGraph
    '''

    response = download_POIs(polygon, custom_filters)
    
    # convert to graph representation and return
    return ox.graph._create_graph([response], retain_all=True)


def bike_infra_from_polygon(polygon: Polygon) -> nx.MultiDiGraph:
    '''
    Downloads network of bike-friendly paths
    
    Parameters
    -------
    polygon: Polygon
        Shapely Polygon object to use as query boundary. 

        
    Returns
    -------
    bike-friendly network within input polygon
    '''    
    
    graphs = []
    for i, (name, params) in enumerate(CONFIG.osm_bike_params.items()):
        try:   
            G = ox.graph_from_polygon(polygon, **params)
            graphs.append(G)
        except ox._errors.EmptyOverpassResponse:
            print(f'No OSM data for {name}')

    return nx.compose_all(graphs) # Returns a single graph


def carall_from_polygon(polygon: Polygon, add_pois: bool = False) -> nx.MultiDiGraph:
    '''
    Downloads network of "driveable" roads
    
    Parameters
    -------
    polygon: Polygon
        Shapely Polygon object to use as query boundary. 
        
    add_pois: bool = False
        Flag to also tag nodes that are nearest to pois identified in `download_pois`. 
        
    Returns
    -------
    driveable network within input polygon
    '''
    
    try: 
        G = ox.graph_from_polygon(polygon, **CONFIG.osm_carall_params['carall'])
    except ox._errors.EmptyOverpassResponse:
        print(f'No OSM data for carall')
        
    if add_pois:
        # Download to POIs
        pois = download_POIs(polygon)
        
        # Find nearest node in G for each POI
        X, Y = [], []
        for node in pois["elements"]:
            X.append(node['lon'])
            Y.append(node['lat'])
        poi_nodes = np.unique(ox.distance.nearest_nodes(G, X=X, Y=Y))
        
        
        # Update those nodes to contain attribute 'poi'=True
        update_dict = {}
        for node in poi_nodes:
            update_dict[node] = True
        nx.set_node_attributes(G, update_dict, name='poi')

    return G

