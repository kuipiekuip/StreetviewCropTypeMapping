import requests
import math
import pandas as pd
import geopandas
from pyproj import Transformer
from tqdm import tqdm
from geopy.distance import geodesic

all_road_points = []

# Constants
EARTH_RADIUS = 6371e3  # in meters
DISTANCE_DELTA = 0.0001  # used for interpolating points along the road
OVERPASS_API_URL = "http://overpass-api.de/api/interpreter"
# Change to own path where .shp file is stored
SHAPEFILE_PATH = r"C:\Users\tijnv\Desktop\StreetviewCropTypeMapping\OSMRoadPoints\bomen\bomen.shp"


def compute_bearing(from_point, to_point):
    """Calculate the bearing from one geographic point to another."""
    lat1, lon1 = map(math.radians, from_point)
    lat2, lon2 = map(math.radians, to_point)

    delta_lon = lon2 - lon1
    x = math.sin(delta_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(
        delta_lon
    )

    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 180) % 360

    return compass_bearing


def find_nearest_road_point_and_compute_bearing(tree_lat, tree_lon, road_data):
    nearest_road_point = None
    min_distance = float("inf")  # Start with infinity
    tree_point = (tree_lat, tree_lon)  # Use a tuple for geopy

    for element in road_data["elements"]:
        if "geometry" in element:
            for node in element["geometry"]:
                road_lat, road_lon = node["lat"], node["lon"]
                road_point = (road_lat, road_lon)  # Use a tuple for geopy
                distance = geodesic(
                    tree_point, road_point
                ).meters  # Calculate distance in meters
                if distance < min_distance:
                    min_distance = distance
                    nearest_road_point = road_point

    if nearest_road_point:
        bearing = compute_bearing(tree_point, nearest_road_point)
        return nearest_road_point, bearing
    else:
        return None, None


def process_shapefile(shapefile_path):
    """Process each geometry in the shapefile and save results."""
    geo_data = geopandas.read_file(shapefile_path)
    geo_data = geo_data.dropna(subset=["CONDITIE"]).reset_index(drop=True)
    for geo_idx, geometry in tqdm(
            enumerate(geo_data.geometry), total=len(geo_data.geometry)
    ):
        if 0 <= geo_idx < 1000:
            process_geometry(geometry, geo_idx, geo_data)


def process_geometry(geometry, geo_idx, geo_data):
    """Process a single geometry from the shapefile."""
    transformer = Transformer.from_crs(f"EPSG:28992", "EPSG:4326", always_xy=True)
    # Perform the transformation
    lon, lat = transformer.transform(geometry.x, geometry.y)
    polygon_query = create_overpass_query(lon, lat)
    road_data = fetch_overpass_data(polygon_query)
    process_road_data(road_data, geo_idx, geo_data)


def create_overpass_query(lon, lat):
    """Create an Overpass API query from exterior coordinates."""
    overpass_query = f"""
    [out:json];
    (
        way(around:10, {lat}, {lon});
    );
    out geom;
    """

    return overpass_query


def fetch_overpass_data(query):
    """Fetch data from the Overpass API."""
    response = requests.get(OVERPASS_API_URL, params={"data": query})
    return response.json()


def process_road_data(road_data, geo_idx, geo_data):
    # Assuming the geometry's coordinates are in the correct order (lat, lon).
    tree_location = geo_data.iloc[geo_idx].geometry.centroid
    tree_lat, tree_lon = tree_location.y, tree_location.x

    # Transform to do distance calculation
    transformer = Transformer.from_crs(f"EPSG:28992", "EPSG:4326", always_xy=True)
    tree_lon, tree_lat = transformer.transform(tree_lon, tree_lat)

    # Fetch and process the nearest road point and bearing.
    nearest_road_point, bearing = find_nearest_road_point_and_compute_bearing(
        tree_lat, tree_lon, road_data
    )

    if nearest_road_point:
        # Prepare the data entry for the CSV.
        entry = (
            geo_idx,  # Geographic index
            nearest_road_point[0],  # Nearest Road Point Latitude
            nearest_road_point[1],  # Nearest Road Point Longitude
            bearing,  # Bearing from Tree to Road Point
            geo_data.iloc[geo_idx]["CONDITIE"],  # Condition (label)
            geo_data["INSPECTIED"][geo_idx])  # Tree inspection date

        all_road_points.append(entry)

    else:
        # Handle the case where no nearest road point is found.
        print(f"No road point found near tree at index {geo_idx}")


def save_to_csv(data, filename, header):
    """Save data to a CSV file using pandas for better handling of mixed data types."""
    # Convert data to DataFrame
    df = pd.DataFrame(data, columns=header.split(","))
    # Save to CSV
    df.to_csv(filename, index=False)


# Main execution
if __name__ == "__main__":
    process_shapefile(SHAPEFILE_PATH)
    save_to_csv(
        all_road_points,
        "roadPoints/RoadPoints.csv",
        "geo_index,rp_lat,rp_lon,b,label,date",
    )
    print("Done")
