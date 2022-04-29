import osmnx as ox
from dataclasses import dataclass

# Update "useful" node tags. This is necessary for some functions in `loader.py`
ox.utils.config(useful_tags_node=["amenity", "name", "shop", "tourism", "leisure"])


@dataclass
class CONFIG:
    osm_bike_params = {
        "bike_cyclewaytrack": {  # cycletrack
            "network_type": "all",
            "custom_filter": '["cycleway"~"track"]',
            "retain_all": True,
        },
        "bike_highwaycycleway": {  # trails
            "network_type": "all",
            "custom_filter": '["highway"~"cycleway"]',
            "retain_all": True,
        },
        "bike_sharedpath": {  # more trails
            "custom_filter": '["highway"~"path|footway"]["bicycle"~"yes|designated"]["surface"!~"ground|unpaved"]',
            "retain_all": True,
        },
        "bike_boulevard": {  # bike boulevards
            "network_type": "all",
            "custom_filter": '["highway"!~"cycleway"]["surface"!~"path"]["bicycle"~"designated"]',
            "retain_all": True,
        },
    }

    osm_carall_params = {
        "carall": {"network_type": "drive", "custom_filter": None, "retain_all": True}
    }

    osm_poi_params = {
        "school": '["amenity"="school"]',
        "convenience_store": '["shop"="convenience"]',
        "supermarket": '["shop"="supermarket"]',
        "park": '["leisure"="park"]',
        "attraction": '["tourism"="attraction"]',
        "museum": '["tourism"="museum"]',
    }

    poi_filepath = "data/POIsRochester.csv"

    median_income_var = "B07011_001E"
