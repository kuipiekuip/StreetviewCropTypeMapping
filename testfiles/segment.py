import torch
from torchvision import models, transforms
from PIL import Image
import matplotlib.pyplot as plt

# Load a pre-trained DeepLabV3 model
model = models.segmentation.deeplabv3_resnet101(pretrained=True)
model.eval()

# Transform the input image
transform = transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

# Load your image
img = Image.open(
    r"C:\Users\kuipe\OneDrive\Bureaublad\TU Delft\Master\Deep Learning\Project\StreetviewCropTypeMapping\images (2)\images\8_Redelijk.jpg"
)
img = transform(img).unsqueeze(0)

# Perform segmentation
with torch.no_grad():
    output = model(img)["out"][0]
output_predictions = output.argmax(0)

# `output_predictions` is the predicted segmentation mask
# mask = output_predictions.cpu().numpy()

# Plot the segmentation mask
r = Image.fromarray(output_predictions.byte().cpu().numpy())
plt.imshow(r)
plt.title("Segmentation Mask")
plt.show()
