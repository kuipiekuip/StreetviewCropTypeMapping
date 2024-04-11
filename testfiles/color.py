import cv2
import numpy as np

# Load the image
image = cv2.imread(
    r"C:\Users\kuipe\OneDrive\Bureaublad\TU Delft\Master\Deep Learning\Project\StreetviewCropTypeMapping\images (2)\images\30928_Slecht.jpg"
)

# Convert to HSV color space
# Convert to HSV color space
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
# Define range for green color in HSV
lower_green = np.array([40, 40, 40])
upper_green = np.array([90, 255, 255])
green_mask = cv2.inRange(hsv, lower_green, upper_green)

# Define range for brown color in HSV
lower_brown = np.array([10, 100, 20])
upper_brown = np.array([20, 255, 200])
brown_mask = cv2.inRange(hsv, lower_brown, upper_brown)

# Combine the masks
combined_mask = cv2.bitwise_or(green_mask, brown_mask)

# Apply the mask to the original image
filtered_image = cv2.bitwise_and(image, image, mask=combined_mask)


# Display the result
cv2.imshow("Filtered Image", filtered_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
