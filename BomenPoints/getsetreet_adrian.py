import requests
import numpy as np
import math
import pandas as pd
import geopandas
from shapely.geometry import LineString, Point, Polygon, MultiPoint
from shapely.ops import nearest_points
from pyproj import Transformer
from tqdm import tqdm
import os

# Constants
EARTH_RADIUS = 6371e3  # in meters
DISTANCE_DELTA = 0.0001  # used for interpolating points along the road
PERPENDICULAR_DISTANCE = 30  # distance for calculating field points
OVERPASS_API_URL = "http://overpass-api.de/api/interpreter"
SHAPEFILE_PATH = r'/Users/marco/Library/CloudStorage/OneDrive-DelftUniversityofTechnology/Control&Simulation/deeplearning/assignment project/StreetviewCropTypeMapping/BomenPoints/bomen.shp'
all_road_points = []

def compute_bearing(from_point, to_point):
    """Calculate the bearing from one geographic point to another."""
    y = math.sin(to_point[1] - from_point[1]) * math.cos(to_point[0])
    x = math.cos(from_point[0]) * math.sin(to_point[0]) - \
        math.sin(from_point[0]) * math.cos(to_point[0]) * math.cos(to_point[1] - from_point[1])
    θ = math.atan2(y, x)
    bearing = (θ * 180 / math.pi + 360) % 360
    return bearing

def compute_point_on_field(from_point, theta, distance):
    """Calculate a point at a certain distance and bearing from a given point."""
    angular_distance = distance / EARTH_RADIUS
    theta = math.radians(theta)
    lat1 = math.radians(from_point[0])
    lon1 = math.radians(from_point[1])
    lat2 = math.asin(math.sin(lat1) * math.cos(angular_distance) + \
                     math.cos(lat1) * math.sin(angular_distance) * math.cos(theta))
    lon2 = lon1 + math.atan2(math.sin(theta) * math.sin(angular_distance) * math.cos(lat1),
                             math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2))
    return (math.degrees(lat2), math.degrees(lon2))

def process_shapefile(shapefile_path):
    """Process each geometry in the shapefile and save results."""
    geo_data = geopandas.read_file(shapefile_path)

    for geo_idx, geometry in tqdm(enumerate(geo_data.geometry), total=len(geo_data.geometry)):
        # print('GEO Index ', geo_idx)
        if geo_idx >= 7:
            process_geometry(geometry, geo_idx)
            if geo_idx == 20:
                break

def process_geometry(geometry, geo_idx):
    """Process a single geometry from the shapefile."""
    transformer = Transformer.from_crs(f"EPSG:28992", "EPSG:4326", always_xy=True)

    # Perform the transformation
    lon, lat = transformer.transform(geometry.x, geometry.y)
    geometry = Point(lon, lat)

    tolerance = 10

    geometry = geometry.simplify(tolerance, preserve_topology=True)

    if geometry.geom_type == "MultiPolygon":
        print("MultiPolygon")
        road_data_combined = {'elements': []}  # Initialize combined road data
        for subgeom in geometry.geoms:  # Iterate through each subpolygon
            subgeom_simplified = subgeom.simplify(tolerance, preserve_topology=True)
            ext_coords = list(subgeom_simplified.exterior.coords)
            polygon_query = create_overpass_query(ext_coords)
            road_data = fetch_overpass_data(polygon_query)
            # print(road_data[])
            road_data_combined['elements'].extend(road_data['elements'])  # Combine road 

    else:
        geometry = geometry.simplify(tolerance, preserve_topology=True)
        lon , lat = geometry.x, geometry.y
        polygon_query = create_overpass_query(lon , lat)
        road_data = fetch_overpass_data(polygon_query)
        # print(road_data)

    process_road_data(road_data, geo_idx, geometry)

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
    response = requests.get(OVERPASS_API_URL, params={'data': query})
    # print(response.json)
    return response.json()

def process_road_data(road_data, geo_idx, geometry):
    """Process road data and save the output to CSV files."""
    road_points, field_points, original_points = [], [], []
    for element in road_data['elements']:
        if element['type'] == 'way':
            keywords = ['highway']
            tags = element.get('tags', {})
            if  any(keyword in tags for keyword in keywords):
                try:
                    road_points = process_way_element(element, road_points, field_points, original_points)
                except Exception as e:
                    print(e)
    if road_points:
        if len(road_points) > 1:
            road_points_geom = MultiPoint([Point(point[1], point[0]) for point in road_points])
        elif len(road_points) == 1:  
            road_points_geom = road_points[0]
    else:
        return
    # print(road_point_map)
    # print(f"Roadpoints: {(road_points)}")
    road_point_map = {(point[0], point[1]): point for point in road_points}
    try:
        nearest_geom = find_nearest_road_point(geometry, road_points_geom)
        all_road_points.extend(road_point_map[(nearest_geom.y, nearest_geom.x)])
    except Exception as e:
        print(e, geo_idx)    

    # save_to_csv(field_points, f"roadPoints/fieldPointsNW4_{geo_idx}.csv", "y,x,b,yr,xr")
    # save_to_csv(original_points, f"roadPoints/osmRoadsNW4_{geo_idx}.csv", "y,x")
    
def find_nearest_road_point(tree_point, road_points_geom):
    """Find the nearest road point to the given tree point using nearest_points."""
    nearest_geom = nearest_points(tree_point, road_points_geom)[1]
    # print(f"Nearest Point: {nearest_geom}")
    return nearest_geom

def process_way_element(element, road_points, field_points, original_points):
    """Process a single way element from the Overpass data."""

    geo = element['geometry']
    way = [(p['lat'], p['lon']) for p in geo]
    original_points.extend(way)
    line = LineString(way)
    distances = np.arange(0, line.length, DISTANCE_DELTA)
    points = [line.interpolate(distance) for distance in distances]

    if line.boundary.length > 1:
        points.append(line.boundary[1])
    if len(points) < 2:
        # print("Not enough points to form a LineString")
        return
    new_line = LineString(points)
    return process_line_points(new_line, road_points, field_points)

def process_line_points(line, road_points, field_points):
    """Process points along a line and compute adjacent field points."""
    old_x, old_y = None, None

    for j, (x, y) in enumerate(line.coords):
        if j > 3 and j< len(line.coords)-3:

            from_point = (old_x, old_y)
            to_point = (x, y)
            bearing = compute_bearing(from_point, to_point)
            p1 = compute_point_on_field(to_point, (bearing + 90) % 360, PERPENDICULAR_DISTANCE)
            p2 = compute_point_on_field(to_point, (bearing + 270) % 360, PERPENDICULAR_DISTANCE)
            field_points.append((p1[0], p1[1], (bearing + 90) % 360, x, y))
            field_points.append((p2[0], p2[1], (bearing + 270) % 360, x, y))
            road_points.append((x, y, bearing, p1[0], p1[1], p2[0], p2[1]))
        old_x, old_y = x, y
    
    return road_points

def save_to_csv(data, filename, header):
    """Save data to a CSV file, ensuring the directory exists."""
    # Extract directory from filename
    directory = os.path.dirname(filename)
    
    # Check if the directory exists, create it if it doesn't
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    # Now save the file as before
    np.savetxt(filename, data, delimiter=",", fmt='%f', header=header, comments='')


# Main execution
if __name__ == "__main__":
    process_shapefile(SHAPEFILE_PATH)
    save_to_csv(all_road_points_trees, "BomenPoints/DelftStreetPoints", "y,x,b,x1,y1,x2,y2")