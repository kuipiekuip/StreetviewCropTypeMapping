import pandas as pd

# Replace 'your_file.csv' with the path to your CSV file
input_csv_path = r'C:\Users\kuipe\OneDrive\Bureaublad\TU Delft\Master\Deep Learning\Project\StreetviewCropTypeMapping\roadPoints\allRoadPointswithGeo.csv'
output_csv_path = r'C:\Users\kuipe\OneDrive\Bureaublad\TU Delft\Master\Deep Learning\Project\StreetviewCropTypeMapping\roadPoints\allRoadPoints.csv'

# Read the CSV file into a DataFrame
df = pd.read_csv(input_csv_path)

# Option 1: Drop the first column by its position
df_modified = df.iloc[:, 1:]

# Option 2: Drop the first column by its name (if you know it)
# column_name = 'name_of_the_first_column'
# df_modified = df.drop(columns=[column_name])

# Write the modified DataFrame to a new CSV file, without the index
df_modified.to_csv(output_csv_path, index=False)
