import pandas as pd
import geopandas
from datetime import date

# Define the path to your CSV file
TREECOVER_FILENAME = 'OSMRoadPoints/roadPoints/allRoadPoints.csv'

# Read the original CSV file
trees = pd.read_csv(TREECOVER_FILENAME)

# Assuming you have another dataset in a shapefile with dates for each geo_index
shapefile_path = 'C:/Users/tijnv/Desktop/StreetviewCropTypeMapping/OSMRoadPoints/bomen/bomen.shp'
geo_data = geopandas.read_file(shapefile_path)

print('before')
# For the CSV file
print(trees.columns)

# For the GeoDataFrame from the shapefile
print(geo_data.columns)

# Assuming your data is already loaded into trees and geo_data
# Reset index to ensure it starts from 0
trees.reset_index(inplace=True, drop=True)
geo_data.reset_index(inplace=True, drop=True)

# Add 'geo_index' to geo_data if it doesn't already exist
geo_data['geo_index'] = geo_data.index

# Now you can proceed to use 'geo_index' for any matching or merging operations
# For example, to add a 'date' column to trees based on geo_data's 'INSPECTIED' column
trees['date'] = geo_data.loc[trees['geo_index'], 'INSPECTIED'].values
print('after')
# For the CSV file
print(trees.columns)

# For the GeoDataFrame from the shapefile
print(geo_data.columns)

print('saving')
UPDATED_TREECOVER_FILENAME = 'OSMRoadPoints/roadPoints/allRoadPoints_updated.csv'
# Save the updated DataFrame to a CSV file
trees.to_csv(UPDATED_TREECOVER_FILENAME, index=False)