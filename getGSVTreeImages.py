import time

import requests

start_time = time.time()

import pandas as pd
import urllib.request, os
import urllib.parse
from tqdm import tqdm
import geopandas
from pyproj import Transformer
from geopy.distance import geodesic
from datetime import datetime

KEY = """AIzaSyB-vx7Dh0LJ2abn8qDPeulCoc4d8w0kodM""" #Insert own API key
key = "&key=" + KEY

# Load RoadPoint.csv
TREECOVER_FILENAME = r"OSMRoadPoints/roadPoints/RoadPoints.csv"
trees = pd.read_csv(TREECOVER_FILENAME)

# Load geo_data

shapefile_path = (
    r"C:\Users\tijnv\Desktop\StreetviewCropTypeMapping\OSMRoadPoints\bomen\bomen.shp"
)
geo_data = geopandas.read_file(shapefile_path)
geo_data = geo_data.dropna(subset=["CONDITIE"]).reset_index(drop=True)
transformer = Transformer.from_crs(f"EPSG:28992", "EPSG:4326", always_xy=True)


def checkInGrowing(image_date_str, check_date_str):
    # Extracting month and year from the dates
    image_date = datetime.strptime(image_date_str, "%Y-%m")
    check_date = datetime.strptime(check_date_str, "%Y-%m-%d")

    # Calculate the month difference
    month_diff_without_year = abs((check_date.month - image_date.month))
    year_diff = abs(check_date.year - image_date.year)
    month_diff = (year_diff) * 12 + (month_diff_without_year)

    return month_diff <= 15 and month_diff_without_year <= 3


def getStreet(lat, lon, SaveLoc, bearing, meta):
    if not os.path.exists(SaveLoc):
        os.makedirs(SaveLoc)

    # Zet conditie heirin de naam van de file
    # query with no bearing anymore, radius and outdoor specified
    MyUrl = (
            "https://maps.googleapis.com/maps/api/streetview?size=640x640&location="
            + str(lat)
            + ","
            + str(lon)
            + "&fov=90&source=outdoor&radius=6"
            + key)
    fi = meta + ".jpg"
    urllib.request.urlretrieve(MyUrl, os.path.join(SaveLoc, fi))


def getMeta(points, myloc, imLimit=0):
    uniqueImageIDs = []
    points = points.reset_index()  # make sure indexes pair with number of rows
    if imLimit == 0:
        imLimit = len(points)

    i = 0
    # for idx, tree in points.iterrows():
    for idx, tree in tqdm(points.iterrows(), total=len(points)):
        # if i <= imLimit and tree['geo_index'] == 13711:   #For pulling speficic tree based on idx
        if i <= imLimit:
            # get tree location from geo_data
            geometry = geo_data.geometry[idx]
            tree_lon, tree_lat = transformer.transform(geometry.x, geometry.y)
            # query with no bearing anymore, radius and outdoor specified
            link = (
                    "https://maps.googleapis.com/maps/api/streetview/metadata?size=640x640&location="
                    + str(tree_lat )
                    + ","
                    + str(tree_lon)
                    + "&fov=80&source=outdoor&radius6"
                    + key
            )
            response = requests.get(link)
            resJson = response.json()
            bearing = float(tree["b"])
            # Did the api give us an image within 5 meters

            if resJson["status"] == "OK":
                gsv_pic_loc = resJson["location"]
                gsv_lat, gsv_lon = gsv_pic_loc["lat"], gsv_pic_loc["lng"]
                #Calculate distance based on distance
                distance = geodesic((tree_lat, tree_lon), (gsv_lat, gsv_lon)).meters
                if checkInGrowing(resJson["date"], tree["date"]):
                    print('growinddate')
                    # Distance check based on coordinates
                    print(distance)
                    if distance <= 5:
                        print('distance ok')
                        # Is image not already pulled for another tree?
                        if resJson["pano_id"] not in uniqueImageIDs:
                            meta = str(tree["geo_index"]) + "_" + str(tree["label"])
                            print(resJson["status"])
                            print(idx)
                            uniqueImageIDs.append(resJson["pano_id"])
                            getStreet(tree_lat, tree_lon, myloc, bearing, meta)
            else:
                print(f"No GSV images found for index: {idx} (within parameters)")
        i += 1


imLimit = 100
getMeta(trees, "images", imLimit=0)
