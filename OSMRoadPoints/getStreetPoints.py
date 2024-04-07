import requests
import numpy as np
import math
import pandas as pd
import geopandas
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import nearest_points
from pyproj import Transformer
from tqdm import tqdm

all_road_points = []
from geopy.distance import geodesic

# Constants
EARTH_RADIUS = 6371e3  # in meters
DISTANCE_DELTA = 0.0001  # used for interpolating points along the road
PERPENDICULAR_DISTANCE = 30  # distance for calculating field points
OVERPASS_API_URL = "http://overpass-api.de/api/interpreter"
SHAPEFILE_PATH = (
    r"C:\Users\tijnv\Desktop\StreetviewCropTypeMapping\OSMRoadPoints\bomen\bomen.shp"
)


# Change bearing because perpendicular
def compute_bearing_old(from_point, to_point):
    """Calculate the bearing from one geographic point to another."""
    y = math.sin(to_point[1] - from_point[1]) * math.cos(to_point[0])
    x = math.cos(from_point[0]) * math.sin(to_point[0]) - math.sin(
        from_point[0]
    ) * math.cos(to_point[0]) * math.cos(to_point[1] - from_point[1])
    θ = math.atan2(y, x)
    bearing = (θ * 180 / math.pi + 360) % 360
    return bearing


def compute_bearing_new(from_point, to_point):
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
        # bearing = compute_bearing(tree_point, nearest_road_point)
        bearing = compute_bearing_new(tree_point, nearest_road_point)
        # print(f'min distance: {min_distance} meters')
        # print(f'tree_lat, tree_lon: {tree_point}')
        # print(f'nearest_road_point: {nearest_road_point}')
        # print(f'bearing: {bearing}')
        return nearest_road_point, bearing
    else:
        return None, None


def compute_point_on_field(from_point, theta, distance):
    """Calculate a point at a certain distance and bearing from a given point."""
    angular_distance = distance / EARTH_RADIUS
    theta = math.radians(theta)
    lat1 = math.radians(from_point[0])
    lon1 = math.radians(from_point[1])
    lat2 = math.asin(
        math.sin(lat1) * math.cos(angular_distance)
        + math.cos(lat1) * math.sin(angular_distance) * math.cos(theta)
    )
    lon2 = lon1 + math.atan2(
        math.sin(theta) * math.sin(angular_distance) * math.cos(lat1),
        math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2),
    )
    return (math.degrees(lat2), math.degrees(lon2))


def process_shapefile(shapefile_path):
    """Process each geometry in the shapefile and save results."""
    geo_data = geopandas.read_file(shapefile_path)
    geo_data = geo_data.dropna(subset=["CONDITIE"]).reset_index(drop=True)
    for geo_idx, geometry in tqdm(
        enumerate(geo_data.geometry), total=len(geo_data.geometry)
    ):
        # if geo_data.iloc[geo_idx]['name_1'] == 'Andhra Pradesh':
        #     print("Geometry ", geo_data.iloc[geo_idx])
        # print('GEO Index ', geo_idx)
        if geo_idx >= 161 and geo_idx < 300:
            # print(geo_data['CONDITIE'][geo_idx])
            # print(geometry, geo_idx, geo_data)
            process_geometry(geometry, geo_idx, geo_data)
            # if geo_idx == 200:
            #     break


def process_geometry(geometry, geo_idx, geo_data):
    """Process a single geometry from the shapefile."""
    transformer = Transformer.from_crs(f"EPSG:28992", "EPSG:4326", always_xy=True)
    # Perform the transformation
    lon, lat = transformer.transform(geometry.x, geometry.y)
    # geometry = Point(lon, lat)
    # lon , lat = geometry.x, geometry.y
    polygon_query = create_overpass_query(lon, lat)
    road_data = fetch_overpass_data(polygon_query)
    # print(road_data)
    # print(f'road_data: {road_data}')
    process_road_data(road_data, geo_idx, geo_data)


def create_overpass_query(lon, lat):
    """Create an Overpass API query from exterior coordinates."""
    overpass_query = f"""
    [out:json];
    (
        way(around:4, {lat}, {lon});
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

    # just transform them here already to do distance calculation
    transformer = Transformer.from_crs(f"EPSG:28992", "EPSG:4326", always_xy=True)
    tree_lon, tree_lat = transformer.transform(tree_lon, tree_lat)

    # Fetch and process the nearest road point and bearing.
    nearest_road_point, bearing = find_nearest_road_point_and_compute_bearing(
        tree_lat, tree_lon, road_data
    )

    if nearest_road_point:
        # debug code for checking nearest road point to tree manually
        # print(f'nearest found, idx:{geo_idx}')
        # print(tree_lat, tree_lon)
        # print(nearest_road_point[0], nearest_road_point[1])

        # Prepare the data entry for the CSV.
        entry = (
            geo_idx,  # Geographic index
            nearest_road_point[0],  # Nearest Road Point Latitude
            nearest_road_point[1],  # Nearest Road Point Longitude
            bearing,  # Bearing from Tree to Road Point
            geo_data.iloc[geo_idx]["CONDITIE"],  # Condition (label)
        )
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
    # save_to_csv(all_road_points, "roadPoints/allRoadPointswithGeo.csv", "geo_idx,y,x,b,x1,y1,x2,y2")
    save_to_csv(
        all_road_points,
        "roadPoints/allRoadPoints.csv",
        "geo_index,rp_lat,rp_lon,b,label",
    )
    print("Done")
