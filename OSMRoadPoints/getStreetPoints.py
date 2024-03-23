import requests
import numpy as np
import math
import pandas as pd
import geopandas
from shapely.geometry import LineString, Point, Polygon
from pyproj import Transformer

# Constants
EARTH_RADIUS = 6371e3  # in meters
DISTANCE_DELTA = 0.0001  # used for interpolating points along the road
PERPENDICULAR_DISTANCE = 30  # distance for calculating field points
OVERPASS_API_URL = "http://overpass-api.de/api/interpreter"
SHAPEFILE_PATH = 'bomen/bomen.shp'
ROADPOINTS_CSV_SAVE_PATH = 'roadPoints'

#Global list for all points
all_points = []


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
    length_geo_data = len(geo_data)
    # print(f'len of shapefile path:{length_geo_data}')
    for geo_idx, geometry in enumerate(geo_data.geometry):
        # if geo_data.iloc[geo_idx]['name_1'] == 'Andhra Pradesh':
        #     print("Geometry ", geo_data.iloc[geo_idx])
        print('GEO Index', geo_idx)
        # print('Percentage index done:' ,geo_idx/length_geo_data)
        if (geo_idx >= 7 and geo_idx <= 200):
            process_geometry(geometry, geo_idx)

def process_geometry(geometry, geo_idx):
    """Process a single geometry from the shapefile."""
    transformer = Transformer.from_crs(f"EPSG:28992", "EPSG:4326", always_xy=True)

    # Perform the transformation
    lon, lat = transformer.transform(geometry.x, geometry.y)
    geometry = Point(lon, lat)

    tolerance = 10

    # if geometry.is_complex:  # Adjust this condition based on your criteria for complexity
    # print(len(geometry))
    # print("Geometry old:", geometry)
    geometry = geometry.simplify(tolerance, preserve_topology=True)
    # print("Geometry:", geometry)
    # print("Post simplify")
    # print(len(geometry))

    if geometry.geom_type == "MultiPolygon":
        # print("MultiPolygon")
        road_data_combined = {'elements': []}  # Initialize combined road data
        for subgeom in geometry.geoms:  # Iterate through each subpolygon
            subgeom_simplified = subgeom.simplify(tolerance, preserve_topology=True)
            ext_coords = list(subgeom_simplified.exterior.coords)
            polygon_query = create_overpass_query(ext_coords)
            road_data = fetch_overpass_data(polygon_query)
            # print(road_data[])
            road_data_combined['elements'].extend(road_data['elements'])  # Combine road data
            # print(road_data)

    else:
        # print(geometry.geom_type)
        # print("NOT a MULTIPOLYGON")
        geometry = geometry.simplify(tolerance, preserve_topology=True)
        lon , lat = geometry.x, geometry.y
        polygon_query = create_overpass_query(lon , lat)
        road_data = fetch_overpass_data(polygon_query)
        # print(road_data)

    process_road_data(road_data, geo_idx)

def create_overpass_query(lon, lat):
    """Create an Overpass API query from exterior coordinates."""
    overpass_query = f"""
    [out:json];
    (
        way(around:10, {lat}, {lon});
    );
    out geom;
    """
    # print(overpass_query)
    return overpass_query

def fetch_overpass_data(query):
    """Fetch data from the Overpass API."""
    response = requests.get(OVERPASS_API_URL, params={'data': query})
    # print(response.status_code)
    # print
    return response.json()


def process_road_data(road_data, geo_idx):
    """Process road data and save the output to global list."""
    road_points, field_points, original_points = [], [], []
    for element in road_data['elements']:
        if element['type'] == 'way':
            keywords = ['highway']
            tags = element.get('tags', {})
            if any(keyword in tags for keyword in keywords):
                try:
                    process_way_element(element, road_points, field_points, original_points)
                except Exception as e:
                    print(e)

    # Append the points to the global list
    all_points.extend(road_points)
    # Extend this logic to field_points and original_points if needed

def process_road_data_old(road_data, geo_idx):
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

    save_to_csv(road_points, f"roadPoints/roadPointsNW4_{geo_idx}.csv", "y,x,b,x1,y1,x2,y2")
    # Add to all points list, to later save to .csv
    # all_points.extend(road_points)
    # save_to_csv(field_points, f"roadPoints/fieldPointsNW4_{geo_idx}.csv", "y,x,b,yr,xr")
    # save_to_csv(original_points, f"roadPoints/osmRoadsNW4_{geo_idx}.csv", "y,x")

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
            road_points.append((x, y, bearing, p1[0], p1[1], p2[0], p2[1]))
        old_x, old_y = x, y

def save_to_csv(data, filename, header):
    """Save data to a CSV file."""
    np.savetxt(filename, data, delimiter=",", fmt='%f', header=header, comments='')

def save_to_one_csv(data, filename, header):
    """Save aggregated data to a single CSV file."""
    # Ensure data is a NumPy array. This step is crucial if data is not already an array.
    array_data = np.array(data)
    np.savetxt(filename, array_data, delimiter=",", fmt='%f', header=header, comments='')


# Main execution
if __name__ == "__main__":
    process_shapefile(SHAPEFILE_PATH)
    #save_to_one_csv(all_points, f"{ROADPOINTS_CSV_SAVE_PATH}/roadPoints.csv", "y,x,b,x1,y1,x2,y2")
    save_to_one_csv(all_points, f"{ROADPOINTS_CSV_SAVE_PATH}/all_roadPoints.csv", "y,x,b,x1,y1,x2,y2")
    #save_to_one_csv(all_points, f"{ROADPOINTS_CSV_SAVE_PATH}/roadPoints.csv", "x,y,b,x1,y1,x2,y2")
