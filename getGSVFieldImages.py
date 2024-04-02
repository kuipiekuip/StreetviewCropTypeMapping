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
from datetime import datetime

KEY = """AIzaSyB-vx7Dh0LJ2abn8qDPeulCoc4d8w0kodM"""
key = "&key=" + KEY

TREECOVER_FILENAME = "roadPoints/testRoadPoints.csv"

trees = pd.read_csv(TREECOVER_FILENAME)


# def checkInGrowing(date, checkDate):
#     print(date)
#     MONTHS = "08, 09, 10, 11, 12, 01,03"
#     # print(date[-2:])
#     if date[-2:] in MONTHS:
#         # print(date[-2:])
#         return True
#     else:
#         return False


def month_diff(month1, month2):
    """Calculate the difference between two months, considering circular nature."""
    diff = abs(month1 - month2)
    return min(diff, 12 - diff)


def checkInGrowing(image_date_str, check_date_str):
    # Extracting month and year from the dates
    image_date = datetime.strptime(image_date_str, "%Y-%m")
    check_date = datetime.strptime(check_date_str, "%Y-%m-%d")
    # print(image_date, check_date)
    # Calculate the month difference
    diff = month_diff(image_date.month, check_date.month)
    # print(diff)
    # Check if the difference is within 3 months
    return diff <= 3


def getStreet(lat, lon, SaveLoc, bearing, meta):

    if not os.path.exists(SaveLoc):
        os.makedirs(SaveLoc)

    # Zet conditie heirin de naam van de file
    heading1 = bearing
    MyUrl = (
        "https://maps.googleapis.com/maps/api/streetview?size=640x640&location="
        + str(lat)
        + ","
        + str(lon)
        + "&fov=90&heading="
        + str(heading1)
        + "&pitch=0"
        + key
    )
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
        if i <= imLimit:

            lon, lat = tree["rp_lon"], tree["rp_lat"]
            # print(lon, lat)
            link = (
                "https://maps.googleapis.com/maps/api/streetview/metadata?size=640x640&location="
                + str(lat)
                + ","
                + str(lon)
                + "&fov=80&heading=0&pitch=0"
                + key
            )
            response = requests.get(link)
            resJson = response.json()
            # print(resJson)
            bearing = float(tree["b"])
            # print(bearing)
            if resJson["status"] == "OK":
                if checkInGrowing(resJson["date"], tree["date"]):
                    if resJson["pano_id"] not in uniqueImageIDs:

                        uniqueImageIDs.append(resJson["pano_id"])
                        meta = str(tree["geo_index"]) + "_" + str(tree["label"])
                        # print(meta)
                        getStreet(lat, lon, myloc, bearing, meta)
            else:
                print("No images found")
        i += 1


imLimit = 100
getMeta(trees, "images", imLimit=0)
