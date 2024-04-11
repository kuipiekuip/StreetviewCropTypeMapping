import geopandas as gpd

# Load the shapefile (this also loads the associated .dbf file)
gdf = gpd.read_file(r'C:\Users\kuipe\OneDrive\Bureaublad\TU Delft\Master\Deep Learning\Project\StreetviewCropTypeMapping\data\bomen.shp')

# Now, gdf contains a GeoDataFrame with your spatial data and labels
print(gdf.head())  # Just to check the first few records

