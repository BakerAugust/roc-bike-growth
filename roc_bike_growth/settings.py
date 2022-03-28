import osmnx as ox
from dataclasses import dataclass

# Update "useful" node tags. This is necessary for some functions in `loader.py`
ox.utils.config(useful_tags_node=["amenity", "name", "shop", "tourism", "leisure"])


@dataclass
class CONFIG:
    osm_bike_params = {
        # Could add this one in later...
        #'car30': {'network_type':'drive', 'custom_filter':'["maxspeed"~"^30$|^20$|^15$|^10$|^5$|^30 mph|^25 mph|^20 mph|^15 mph|^10 mph|^5 mph"]', 'retain_all': True},
        "bike_cyclewaylane": {
            "network_type": "bike",
            "custom_filter": '["cycleway"~"lane"]',
            "retain_all": True,
        },
        "bike_cyclewaytrack": {
            "network_type": "bike",
            "custom_filter": '["cycleway"~"track"]',
            "retain_all": True,
        },
        "bike_highwaycycleway": {
            "network_type": "all",
            "custom_filter": '["highway"~"cycleway"]',
            "retain_all": True,
        },
        "bike_designatedpath": {
            "network_type": "all",
            "custom_filter": '["highway"~"path"]["bicycle"~"designated"]',
            "retain_all": True,
        },
        "bike_sharedpath": {
            "custom_filter": '["highway"~"path"]["bicycle"~"yes"]["surface"!~"ground"]',
            "retain_all": True,
        },
        "bike_cyclewayrighttrack": {
            "network_type": "bike",
            "custom_filter": '["cycleway:right"~"track"]',
            "retain_all": True,
        },
        "bike_cyclewaylefttrack": {
            "network_type": "bike",
            "custom_filter": '["cycleway:left"~"track"]',
            "retain_all": True,
        },
        "bike_cyclestreet": {
            "network_type": "bike",
            "custom_filter": '["cyclestreet"]',
            "retain_all": True,
        },
        "bike_bicycleroad": {
            "network_type": "bike",
            "custom_filter": '["bicycle_road"]',
            "retain_all": True,
        },
        "bike_sharrow": {
            "network_type": "bike",
            "custom_filter": '["cycleway"~"shared_lane"]',
            "retain_all": True,
        },
        "bike_livingstreet": {
            "network_type": "bike",
            "custom_filter": '["highway"~"living_street"]',
            "retain_all": True,
        },
    }

    osm_carall_params = {
        "carall": {"network_type": "drive", "custom_filter": None, "retain_all": False}
    }

    osm_poi_params = {
        "school": '["amenity"="school"]',
        "convenience_store": '["shop"="convenience"]',
        "supermarket": '["shop"="supermarket"]',
        "park": '["leisure"="park"]',
        "attraction": '["tourism"="attraction"]',
        "museum": '["tourism"="museum"]',
    }
