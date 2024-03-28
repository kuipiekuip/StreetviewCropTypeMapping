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

# Constants
EARTH_RADIUS = 6371e3  # in meters
DISTANCE_DELTA = 0.0001  # used for interpolating points along the road
PERPENDICULAR_DISTANCE = 30  # distance for calculating field points
OVERPASS_API_URL = "http://overpass-api.de/api/interpreter"
SHAPEFILE_PATH = r'C:\Users\kuipe\OneDrive\Bureaublad\TU Delft\Master\Deep Learning\Project\StreetviewCropTypeMapping\data\bomen.shp'

# Change bearing because perpendicular
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
    geo_data = geo_data.dropna(subset=['CONDITIE']).reset_index(drop=True)
    for geo_idx, geometry in tqdm(enumerate(geo_data.geometry),total=len(geo_data.geometry)):
        # if geo_data.iloc[geo_idx]['name_1'] == 'Andhra Pradesh':
        #     print("Geometry ", geo_data.iloc[geo_idx])
        # print('GEO Index ', geo_idx)
        if geo_idx >= 7:
            # print(geo_data['CONDITIE'][geo_idx])
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
    response = requests.get(OVERPASS_API_URL, params={'data': query})
    return response.json()

def process_road_data(road_data, geo_idx, geo_data):
    """Process road data and save the output to CSV files."""
    road_points, field_points, original_points = [], [], []

    for element in road_data['elements']:
        if element['type'] == 'way':
            keywords = ['highway']
            tags = element.get('tags', {})
            if  any(keyword in tags for keyword in keywords):
                try:
                    process_way_element(element, road_points, field_points, original_points)
                    
                except Exception as e:
                    print(e)

    nearest_road_point_info = None
    min_distance = float('inf')
    for point in road_points:
        # Assuming point format is (x, y, bearing)
        x, y, bearing = point
        road_point = Point(x, y)
        distance = geo_data['geometry'][geo_idx].distance(road_point)
        if distance < min_distance:
            min_distance = distance
            nearest_road_point_info = (x, y, bearing)  # Store the nearest point with its bearing

    if nearest_road_point_info:
        # Append the nearest road point info, which includes bearing
        all_road_points.append((geo_idx,) + nearest_road_point_info + (geo_data['CONDITIE'][geo_idx	],))
    # if len(road_points) > 0:  
    #     all_road_points.append((geo_idx,) + road_points[0] + (label,))           

    else:
        return
        # print(geo_idx, "No road points found in this geometry")


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
    process_line_points(new_line, road_points, field_points)

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
            road_points.append((x, y, bearing))
        old_x, old_y = x, y

def save_to_csv(data, filename, header):
    """Save data to a CSV file using pandas for better handling of mixed data types."""
    # Convert data to DataFrame
    df = pd.DataFrame(data, columns=header.split(","))
    
    # Save to CSV
    df.to_csv(filename, index=False)

# Main execution
if __name__ == "__main__":
    process_shapefile(SHAPEFILE_PATH)
    print(all_road_points[0])
    # save_to_csv(all_road_points, "roadPoints/allRoadPointswithGeo.csv", "geo_idx,y,x,b,x1,y1,x2,y2")
    save_to_csv(all_road_points, "roadPoints/allRoadPoints.csv", "geo_index,rp_lat,rp_lon,b,label")
    print("Done")