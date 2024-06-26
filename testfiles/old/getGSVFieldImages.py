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


KEY = """AIzaSyB-vx7Dh0LJ2abn8qDPeulCoc4d8w0kodM"""
key = "&key=" + KEY

TREECOVER_FILENAME = 'OSMRoadPoints/roadPoints/allRoadPoints.csv'

trees = pd.read_csv(TREECOVER_FILENAME)


def checkInGrowing(date):
    # print(date)
    MONTHS = '08, 09, 10, 11, 12, 01, 03'
    # print(date[-2:])
    if date[-2:] in MONTHS:
        # print(date[-2:])
        return True
    else:
        return False

def getStreet(lat,lon,SaveLoc, bearing, meta):

    if not os.path.exists(SaveLoc):
        os.makedirs(SaveLoc)

    # Zet conditie heirin de naam van de file
    heading1 = bearing
    MyUrl = "https://maps.googleapis.com/maps/api/streetview?size=640x640&location="+str(lat)+","+str(lon)+"&fov=90&heading="+str(heading1)+"&pitch=0" + key
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
        if i <= imLimit and tree['geo_index'] == 13711:

            lon, lat = tree['rp_lon'], tree['rp_lat']
            # print(lon, lat)
            link = "https://maps.googleapis.com/maps/api/streetview/metadata?size=640x640&location="+str(lat)+","+str(lon)+"&fov=80&heading=0&pitch=0" + key
            response = requests.get(link)
            resJson = response.json()
            # print(resJson)
            bearing = float(tree['b'])
            # print(bearing)
            gsv_pic_loc = resJson['location']
            print(f'gsv pic location: {gsv_pic_loc}')
            if resJson['status'] ==  'OK':
                if checkInGrowing(resJson['date']):
                    if resJson['pano_id'] not in uniqueImageIDs:
                        
                        uniqueImageIDs.append(resJson['pano_id'])
                        meta = str(tree['geo_index']) + '_' + str(tree['label']) 
                        # print(meta)
                        getStreet(lat,lon, myloc, bearing, meta)
            else:
                print('No images found')
        i+=1

imLimit = 100
getMeta(trees, 'images_test', imLimit=0)