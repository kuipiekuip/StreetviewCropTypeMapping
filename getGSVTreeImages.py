import requests
import numpy as np
import time
import shutil

start_time = time.time()

import pandas as pd
import csv
import urllib.request, os
import urllib.parse
import numpy as np
import streetview
import math
from tqdm import tqdm
import geopandas
from pyproj import Transformer
from geopy.distance import geodesic
from datetime import datetime

KEY = """AIzaSyB-vx7Dh0LJ2abn8qDPeulCoc4d8w0kodM"""
key = "&key=" + KEY

#Load roadpoint file
TREECOVER_FILENAME = 'OSMRoadPoints/roadPoints/allRoadPoints_updated.csv'
shapefile_path = r'C:\Users\tijnv\Desktop\StreetviewCropTypeMapping\OSMRoadPoints\bomen\bomen.shp'
trees = pd.read_csv(TREECOVER_FILENAME)

#Load geo_data
geo_data = geopandas.read_file(shapefile_path)
geo_data = geo_data.dropna(subset=['CONDITIE']).reset_index(drop=True)
transformer = Transformer.from_crs(f"EPSG:28992", "EPSG:4326", always_xy=True)

def month_diff(month1, month2):
    """Calculate the difference between two months, considering circular nature."""
    diff = abs(month1 - month2)
    return min(diff, 12 - diff)


def checkInGrowing(image_date_str, check_date_str):
    # Extracting month and year from the dates
    image_date = datetime.strptime(image_date_str, "%Y-%m")
    check_date = datetime.strptime(check_date_str, "%Y-%m-%d")
    # Calculate the month difference
    diff = month_diff(image_date.month, check_date.month)

    # small debug for tweaking
    # if diff > 3:
    #     print(f'Diff higher then 3, diff: {diff}')
    # Check if the difference is within 3 months
    return diff <= 3

def getStreet(lat,lon,SaveLoc, bearing, meta):
    if not os.path.exists(SaveLoc):
        os.makedirs(SaveLoc)

    # Zet conditie heirin de naam van de file
    # query with no bearing anymore, radius and outdoor specified
    MyUrl = "https://maps.googleapis.com/maps/api/streetview?size=640x640&location="+str(lat)+","+str(lon)+"&fov=90&source=outdoor&radius=10" + key
    fi = meta + ".jpg"
    urllib.request.urlretrieve(MyUrl, os.path.join(SaveLoc,fi))

def getMeta(points, myloc, imLimit=0):
    uniqueImageIDs= []
    points = points.reset_index()  # make sure indexes pair with number of rows
    if imLimit == 0:
        imLimit = len(points)

    i = 0
    # for idx, tree in points.iterrows():
    for idx, tree in tqdm(points.iterrows(), total=len(points)):
        # if i <= imLimit and tree['geo_index'] == 13711:   #if you want to just pull a specific tree
        if i <= imLimit:
            #get tree location from geo_data
            geometry = geo_data.geometry[idx]
            lon, lat = transformer.transform(geometry.x, geometry.y)

            #query with no bearing anymore, radius and outdoor specified
            link = "https://maps.googleapis.com/maps/api/streetview/metadata?size=640x640&location=" + str(lat) + "," + str(lon) + "&fov=80&source=outdoor&radius=10" + key
            response = requests.get(link)
            resJson = response.json()
            bearing = float(tree['b'])
            idx_tree = tree['geo_index']
            # is there a GSV image in a radius of 10 m from the tree coordinate?
            if resJson['status'] ==  'OK':
                if checkInGrowing(resJson["date"], tree["date"]):
                    # manual distance check
                    gsv_pic_loc = resJson['location']
                    gsv_lat, gsv_lon = gsv_pic_loc['lat'], gsv_pic_loc['lng']
                    distance = geodesic((lat, lon), (gsv_lat, gsv_lon)).meters
                    if distance <= 10:
                        if resJson['pano_id'] not in uniqueImageIDs:
                            meta = str(tree['geo_index']) + '_' + str(tree['label'])
                            uniqueImageIDs.append(resJson['pano_id'])
                            getStreet(lat,lon, myloc, bearing, meta)

                            # debug for tweaking
                            # print(resJson)
                            # print(f'idx:{idx_tree}')
                            # print(f'gsv pic location: {gsv_lat, gsv_lon}')
                            # print(f'tree coordinates: {lat, lon}')
                            # print(f'distance photo and tree: {distance}')
                            # print(tree["date"])
            else:
                # No image found in radius of 10 meter around the tree coordinate
                print(f'No GSV images found for index: {idx_tree} (within parameters)')
        i+=1

imLimit = 100
getMeta(trees, 'images', imLimit=0)