import cv2
import numpy as np
from PIL import Image

# Read logo_raw
img = cv2.imread(r"frontend\public\assets\images\logo_raw.png")
h, w, _ = img.shape

# 1. Remove the bottom circular arc:
# In logo_raw, the bottom arc starts below the swoosh.
# The swoosh has yellow / red colors. The lowest tip of the swoosh is at x ~ 200, y ~ 570.
# The arc starts around x=330, y=520 and curves down to x=800, y=600.
# Let's cleanly paint the arc region with black in img:
for y in range(500, h):
    for x in range(320, w):
        # The swoosh ends before x=850, y=490 on the right side, but has a yellow tail extending to x=830, y=480.
        # Below y=500 and x > 300 is definitely the arc!
        img[y, x] = [28, 28, 28]

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# The logo's outer cream/white contour has gray > 115.
# Let's detect the contour of the logo.
# We threshold the cream border:
cream = cv2.inRange(img, np.array([50, 70, 100]), np.array([210, 255, 255]))
# Also bright whites:
bright = cv2.inRange(gray, 100, 255)
logo_features = cv2.bitwise_or(cream, bright)

# Connect the contour
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
closed = cv2.morphologyEx(logo_features, cv2.MORPH_CLOSE, kernel)

# Find all contours
contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

mask = np.zeros((h, w), dtype=np.uint8)
for c in contours:
    if cv2.contourArea(c) > 2000:
        cv2.drawContours(mask, [c], -1, 255, -1)

# Smooth mask edges slightly with Gaussian Blur to get clean antialiasing
mask_blur = cv2.GaussianBlur(mask, (5, 5), 0)

# Crop the mask and image to tight bounding box of the logo
y_indices, x_indices = np.where(mask > 0)
min_y, max_y = np.min(y_indices), np.max(y_indices)
min_x, max_x = np.min(x_indices), np.max(x_indices)

# Add small padding
pad = 15
min_y = max(0, min_y - pad)
max_y = min(h, max_y + pad)
min_x = max(0, min_x - pad)
max_x = min(w, max_x + pad)

cropped_img = img[min_y:max_y, min_x:max_x]
cropped_mask = mask_blur[min_y:max_y, min_x:max_x]

b, g, r = cv2.split(cropped_img)
rgba = cv2.merge([b, g, r, cropped_mask])

# Save transparent logo
cv2.imwrite(r"frontend\public\assets\images\logo_transparent.png", rgba)
cv2.imwrite(r"frontend\public\logo.png", rgba)
cv2.imwrite(r"frontend\src\assets\logo.png", rgba)

# Create a circular / rounded icon for favicon and app badge
ch, cw, _ = rgba.shape
size = max(ch, cw) + 40
badge = np.zeros((size, size, 4), dtype=np.uint8)

# Center in badge
oy = (size - ch) // 2
ox = (size - cw) // 2
badge[oy:oy+ch, ox:ox+cw] = rgba

# Save circular/square icons
cv2.imwrite(r"frontend\public\assets\images\logo_badge.png", badge)
cv2.imwrite(r"frontend\public\favicon.png", cv2.resize(badge, (192, 192), interpolation=cv2.INTER_AREA))

print("Transparent logo & icons created successfully! Dimensions:", cw, "x", ch)
