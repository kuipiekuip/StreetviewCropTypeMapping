
### Classifying Tree Health in Delft

This toolkit consists of three main scripts designed to extract and analyze street view images of trees based on their geographic points and conditions:
1. `getStreetPoints.py`: Generates a CSV file with road point coordinates of trees and relevant metadata.
2. `getGSVTreeImages.py`: Downloads images from Google Street View using coordinates and ensures they match the date of the tree's health assessment.
3. `imageSegmentation.py`: Processes downloaded images to segment and highlight tree areas, blurring other parts.
4. `binaryTreeClassifier.ipynb`: Trains a binary classifier to filter out GSV images that do not contain a clear view of a tree.

5. We would like to refer to the blog post we created as well! [Documentation](https://example.com)

### Built With

This project utilizes a range of libraries and frameworks:
* [Python](https://python.org)
* [Pandas](https://pandas.pydata.org/)
* [GeoPandas](http://geopandas.org/)
* [Requests](https://requests.readthedocs.io/en/master/)
* [OpenCV](https://opencv.org/)
* [Numpy](https://numpy.org/)
* [Pillow](https://python-pillow.org/)
* [TQDM](https://tqdm.github.io/)
* [PyProj](https://pyproj4.github.io/pyproj/stable/)
* [Geopy](https://geopy.readthedocs.io/en/stable/)

<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple steps.

### Prerequisites

Make sure you have Python installed and then install the necessary libraries using the following command:
```sh
pip install numpy pandas geopandas opencv-python requests tqdm pillow pyproj geopy
```

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/kuipiekuip/StreetviewCropTypeMapping.git
   ```
2. Install Python packages
   ```sh
   pip install -r requirements.txt
   ```

<!-- USAGE EXAMPLES -->
## Usage

### `getStreetPoints.py`
- **Purpose**: Generates a CSV with road point coordinates and metadata.
- **Key Parameters**: File path for the shapefile (must be absolute).
- **Output**: `RoadPoints.csv` containing coordinates and metadata.

### `getGSVTreeImages.py`
- **Purpose**: Downloads Google Street View images based on coordinates from the CSV.
- **Key Parameters**:
  - Google Street View API Key.
  - `maxDistance`: The maximum distance to consider for matching tree locations (default is 5 meters).
  - Absolute path for the shapefile.
- **Output**: Downloads images and saves them to a specified directory.

### `imageSegmentation.py`
- **Purpose**: Segments and highlights areas with trees in the downloaded images, blurring other parts.
- **Key Parameters**:
  - Roboflow API key.
  - Directories for input images and output segmented images.
- **Output**: Segmented images saved in the specified directory.

### `binaryTreeClassifier.ipynb`
- **Purpose**: Trains a binary classifier to filter out GSV images that do not contain a clear view of a tree.
- **Key Parameters**:
  - Train, validate and test data which can be found in `TreeOrNoTree-Data.zip`
- **Output**: Classification of the test dataset.

We would like to refer to the blog post we created as well! [Documentation](https://example.com)
<!-- CONTACT -->
## Contact
Tijn Vennink: tijnvennink@gmail.com

Project Link: [https://github.com/kuipiekuip/StreetviewCropTypeMapping](https://github.com/kuipiekuip/StreetviewCropTypeMapping)

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments
- [Google Street View API](https://developers.google.com/maps/documentation/streetview/overview)
- [Roboflow](https://roboflow.com/)
- [GeoPy](https://geopy.readthedocs.io/en/stable/)
