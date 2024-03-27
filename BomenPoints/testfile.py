import geopandas as gpd

shapefile_path = 'BomenPoints/bomen.shp'

gdf = gpd.read_file(shapefile_path)


selected_columns = gdf[['CONDITIE', 'geometry']] 
selected_columns['longitude'] = selected_columns['geometry'].x
selected_columns['latitude'] = selected_columns['geometry'].y
selected_columns = selected_columns.drop(['geometry'], axis=1)


print(selected_columns.head(20))