# from roboflow import Roboflow

# rf = Roboflow(api_key="1FdTZbO8LVb5NAChYSXJ")
# project = rf.workspace().project("tree.1")
# model = project.version(1).model

# path = r"C:\Users\kuipe\OneDrive\Bureaublad\TU Delft\Master\Deep Learning\Project\StreetviewCropTypeMapping\images (2)\images\31433_Matig.jpg"
# # infer on a local image
# print(model.predict(path).json())

# # infer on an image hosted elsewhere
# # print(model.predict("URL_OF_YOUR_IMAGE").json())

# save an image annotated with your predictions
# model.predict(path).save("prediction.jpg")
from roboflow import Roboflow
import os
import glob
from PIL import Image
import numpy as np
import cv2
import base64
from io import BytesIO
from tqdm import tqdm

# Initialize Roboflow model
rf = Roboflow(api_key="1FdTZbO8LVb5NAChYSXJ")
project = rf.workspace().project("tree.1")
model = project.version(1).model

# Define your source and destination directories
source_dir = "images"
destination_dir = "segmented_images"

# List all jpg images in the source directory
print(glob.glob(os.path.join(source_dir, "*.jpg")))
image_files = glob.glob(os.path.join(source_dir, "*.jpg"))
print(image_files)
# Process images with a progress bar
for img_path in tqdm(image_files, desc="Processing Images"):
    # Infer on the local image
    result = model.predict(img_path)

    # Construct the path to save the segmented image
    # Preserve the original file name, but save in the destination directory
    base_name = os.path.basename(img_path)
    save_path = os.path.join(destination_dir, base_name)

    # Save the image annotated with predictions
    result.save(save_path)

    # Optionally, you can print the save_path for each processed image
    # print(f"Processed and saved: {save_path}")
