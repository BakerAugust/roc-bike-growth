import osmnx as ox
import networkx as nx
import numpy as np
import geopandas as gpd
from roc_bike_growth.settings import CONFIG
from roc_bike_growth.graph_utils import get_street_segment
from shapely.geometry import Polygon, MultiPolygon, LineString, Point

from typing import List, Union


def download_osm_POIs(
    polygon: Union[Polygon, MultiPolygon], custom_filters: dict = CONFIG.osm_poi_params
) -> dict:
    """
    Queries overpass for nodes in polygon with matching filters and returns json response.

    Parameters
    -------
    polygon: Polygon | MultiPolygon
        Shapely Polygon or MultiPolygon object to use as query boundary.
    custom_filters: dict
        dict of name : custom filters for the nodes. E.x. '["amenity"="school"]'

    Returns
    -------
    dict

    """

    # format overpass query
    overpass_settings = ox.downloader._make_overpass_settings()

    # convert polygon to Overpass poly strings
    overpass_polygon_strs = []
    if isinstance(polygon, MultiPolygon):  # Split apart MultiPolygon
        for poly in polygon.geoms:
            overpass_polygon_strs.append(
                ox.downloader._make_overpass_polygon_coord_strs(poly)
            )

    elif isinstance(polygon, Polygon):
        overpass_polygon_strs.append(
            ox.downloader._make_overpass_polygon_coord_strs(polygon)
        )

    else:
        raise TypeError(f"polygon geometry of type {type(polygon)} not accepted.")

    # Construct filters as strings
    components = []
    for poly in overpass_polygon_strs:
        for custom_filter in custom_filters.values():
            components.append(f'node{custom_filter}(poly:"{poly[0]}")')

    # Do overpass query
    query = f"{overpass_settings};({';'.join(components)};>;);out;"

    return ox.downloader.overpass_request(data={"data": query})


def POI_graph_from_polygon(
    polygon: Polygon, custom_filters: dict = CONFIG.osm_poi_params
) -> Union[nx.MultiDiGraph, list]:
    """
    Queries overpass for nodes in polygon with matching filters and returns a graph.

    Parameters
    -------
    polygon: Polygon
        Shapely Polygon object to use as query boundary.
    custom_filters: dict
        dict of name : custom filters for the nodes. E.x. '["amenity"="school"]'

    Returns
    -------
    nx.MultiDiGraph
    """

    response = download_osm_POIs(polygon, custom_filters)

    # convert to graph representation and return
    return ox.graph._create_graph([response], retain_all=True)


def POIs_from_file(filepath: str) -> gpd.GeoDataFrame:
    """
    Loads pois from file and convert projection.
    """
    gdf = gpd.read_file(filepath)

    def address2point(address: str) -> Point:
        """
        Geocodes address and converts to Point
        """
        try:
            lat, lon = ox.geocoder.geocode(f"{address} rochester ny")
        except Exception as e:
            print(f"Exception at {address}. This point will be dropped:")
            print(f" {e}")
            return

        return Point(lon, lat)

    return gdf.assign(geometry=gdf["Address"].apply(address2point)).dropna(
        subset=["geometry"]
    )


def _fill_edge_geometry(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """
    Naive filling of empty edge geometries. For edge (u,v), creates LineString from u to v.

    Adapted from https://github.com/gboeing/osmnx/blob/main/osmnx/utils_graph.py

    Parameters
    -------
    G: nx.MultiDiGraph
        graph

    Returns
    -------
    G with edges geometries added in.
    """
    x_lookup = nx.get_node_attributes(G, "x")
    y_lookup = nx.get_node_attributes(G, "y")
    eattrs = {}
    for u, v, k, data in G.edges(keys=True, data=True):
        if data.get("geometry", None) is None:
            geom = LineString(
                (
                    Point((x_lookup[u], y_lookup[u])),
                    Point((x_lookup[v], y_lookup[v])),
                )
            )
            eattrs[(u, v, k)] = {"geometry": geom}

    nx.set_edge_attributes(G, eattrs)
    return G


def load_roc_in_progress(carall: nx.MultiDiGraph = None) -> nx.MultiDiGraph:
    """
    Downloads rochester in-progress bike infrastructure graph.

    Parameters
    -------
    carall: nx.MultiDiGraph
        Rochester carall graph. Can be passed-in to avoid downloading again.
    """

    segments = [  # street, src_intersection, dest_intersection
        # East main project
        ("east main street", "goodman street", "alexander street"),
        # North inner loop approximation
        ("university avenue", "pitkin street", "north street"),
        ("andrews street", "state street", "north street"),
        ("state street", "andrews street", "church street"),
        ("church street", "state street", "north plymouth avenue"),
        ("north plymouth avenue", "church street", "allen street"),
        ("allen street", "north washington street", "north plymouth avenue"),
    ]

    # We could probably eliminate the need to download carall here by refactoring get_street_segment.
    # Should probably just refactor this whole thing into a class...
    if carall is None:
        carall = carall_from_polygon(ox.geocode_to_gdf("rochester, ny").geometry[0])
    nodes = []
    for street, src, dest in segments:
        nodes += get_street_segment(carall, street, src, dest)

    roc_in_progress = carall.subgraph(set(nodes)).copy()

    return roc_in_progress


def load_roc_proposed(
    priority: int = 0, carall: nx.MultiDiGraph = None
) -> nx.MultiDiGraph:
    """
    Downloads proposed rochester bike infrastructure graph based on the
    2015 bikeable cities report.

    Parameters
    -------
    priority: int = 0
        Which priority of proposed bike infrastructure to load. Prioriy 1 loads
        priority "i" from reoprt. Priority 2 loads "ii". All other values load
        both. Default=0.
    carall: nx.MultiDiGraph
        Rochester carall graph. Can be passed-in to avoid downloading again.
    """

    # Priority i from bikeable cities report
    segments_i = [  # street, src_intersection, dest_intersection
        ("broad street", "smith street", "allen street"),
        ("genesee street", "melrose street", "elmwood avenue"),
        ("portland avenue", "north street", "central park"),
        ("monroe avenue", "howell street", "alexander street"),
        ("monroe avenue", "goodman street", "highland avenue"),
    ]

    # Priority ii from Bikeable cities report
    segments_ii = [
        ("south avenue", "mount hope", "elmwood avenue"),
        ("lyell avenue", "lake avenue", "fairgate street"),
        ("dewey avenue", "driving park avenue", "lyell avenue"),
        # Broad street
        ("east broad street", "chestnut street", "exchange"),
        ("west broad street", "exchange", "west main street"),
        ("west broad street", "west main street", "lyell avenue"),
        ("west main street", "cascade drive", "brown street"),
        ("driving park avenue", "argo park", "carthage dr"),
        ("avenue e", "carthage dr", "conkey avenue"),
        ("webster avenue", "garson avenue", "bay street"),
        ("chestnut street", "monroe avenue", "east avenue"),
        ("north chestnut street", "university avenue", "east avenue"),
        ("joseph avenue", "norton street", "cumberland street"),
        ("elmwood avenue", "mount hope", "south goodman"),
    ]

    if priority == 1:
        segments = segments_i
    elif priority == 2:
        segments = segments_ii
    else:
        segments = segments_i + segments_ii

    # We could probably eliminate the need to download carall here by refactoring get_street_segment.
    # Should probably just refactor this whole thing into a class...
    if carall is None:
        carall = carall_from_polygon(ox.geocode_to_gdf("rochester, ny").geometry[0])
    nodes = []
    for street, src, dest in segments:
        nodes += get_street_segment(carall, street, src, dest)

    return carall.subgraph(set(nodes)).copy()


def bike_infra_from_polygon(
    polygon: Polygon,
    custom_filters: dict = CONFIG.osm_bike_params,
    compose_all: bool = True,
    fill_edge_geometry: bool = True,
    buffer_dist: float = 100,
    add_roc_in_progress: bool = True,
) -> nx.MultiDiGraph:
    """
    Downloads network of bike-friendly paths

    Parameters
    -------
    polygon: Polygon
        Shapely Polygon object to use as query boundary.
    compose_all: bool = True
        If true, compose all into a signle graph
    fill_edge_geometry: bool = True
        Flag to fill missing edge geometries. For edge (u,v), creates LineString from u to v.
    buffer_dist: float = 100
        Buffer to pad the query polygon in meters
    add_roc_in_progress: bool = True
        Manual addition of "in-progress" bike infrastructure in Rochester.

    Returns
    -------
    bike-friendly network within input polygon
    """

    graphs = []
    names = []

    if buffer_dist:
        poly_proj, crs_utm = ox.projection.project_geometry(polygon)
        poly_proj_buff = poly_proj.buffer(buffer_dist)
        polygon, _ = ox.projection.project_geometry(
            poly_proj_buff, crs=crs_utm, to_latlong=True
        )

    for name, params in custom_filters.items():
        try:
            G = ox.graph_from_polygon(polygon, truncate_by_edge=True, **params)
            nx.set_edge_attributes(G, name, "bike_infrastructure_type")
            graphs.append(G)
            names.append(name)
        except ox._errors.EmptyOverpassResponse:
            print(f"No OSM data for {name}")

    if add_roc_in_progress:
        roc_in_progress = load_roc_in_progress()

        # add to cycletrack
        cycleway_idx = names.index("bike_cyclewaytrack")
        cycleway_g = graphs[cycleway_idx]
        graphs[cycleway_idx] = nx.compose_all([cycleway_g, roc_in_progress])

    if compose_all:
        G = nx.compose_all(graphs)  # Returns a single graph
        if fill_edge_geometry:
            return _fill_edge_geometry(G)
        else:
            return G
    else:
        if fill_edge_geometry:
            return list(zip(names, [_fill_edge_geometry(g) for g in graphs]))
        else:
            return list(zip(names, graphs))


def carall_from_polygon(
    polygon: Polygon, add_pois: bool = False, fill_edge_geometry: bool = True
) -> nx.MultiDiGraph:
    """
    Downloads network of "driveable" roads

    Parameters
    -------
    polygon: Polygon
        Shapely Polygon object to use as query boundary.

    add_pois: bool = False
        Flag to also tag nodes that are nearest to pois identified in `download_osm_POIs`.

    fill_edge_geometry: bool = True
        Flag to fill missing edge geometries. For edge (u,v), creates LineString from u to v.

    Returns
    -------
    driveable network within input polygon
    """

    try:
        G = ox.graph_from_polygon(polygon, **CONFIG.osm_carall_params["carall"])

        if add_pois:
            # Download osm POIs
            pois = download_osm_POIs(polygon)

            # Find nearest node in G for each POI
            X, Y = [], []
            for node in pois["elements"]:
                X.append(node["lon"])
                Y.append(node["lat"])

            # Add POIs from file
            gdf = POIs_from_file(CONFIG.poi_filepath)
            for _, row in gdf.iterrows():
                x, y = row["geometry"].coords[0]
                X.append(x)
                Y.append(y)

            poi_nodes = np.unique(ox.distance.nearest_nodes(G, X=X, Y=Y))

            # Update those nodes to contain attribute 'poi'=True
            update_dict = {}
            for node in poi_nodes:
                update_dict[node] = True
            nx.set_node_attributes(G, update_dict, name="poi")

        if fill_edge_geometry:
            G = _fill_edge_geometry(G)

        return G

    except ox._errors.EmptyOverpassResponse:
        print(f"No OSM data for carall")
        return
