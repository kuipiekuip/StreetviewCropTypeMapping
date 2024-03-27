import pandas as pd

# Replace 'your_file.csv' with the path to your CSV file
input_csv_path = r'C:\Users\kuipe\OneDrive\Bureaublad\TU Delft\Master\Deep Learning\Project\StreetviewCropTypeMapping\roadPoints\allRoadPoints.csv'
output_csv_path = r'C:\Users\kuipe\OneDrive\Bureaublad\TU Delft\Master\Deep Learning\Project\StreetviewCropTypeMapping\roadPoints\clean.csv'
# Read the CSV file into a DataFrame
df = pd.read_csv(input_csv_path)

# Specify the column names to consider when looking for duplicates (exclude the column that makes them unique)
columns_to_consider = ['column1', 'column2', 'column3']  # Replace these with your actual column names

# Remove duplicate rows based on the specified columns
df_no_duplicates = df.drop_duplicates()

# Write the DataFrame with duplicates removed to a new CSV file, without the index
df_no_duplicates.to_csv(output_csv_path, index=False)
