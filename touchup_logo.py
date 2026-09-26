import cv2
import numpy as np

# Load the saved logo_transparent.png
logo = cv2.imread(r"frontend\public\assets\images\logo_transparent.png", cv2.IMREAD_UNCHANGED)
h, w, c = logo.shape

# Clean the tiny orange sliver at the bottom:
# Look at the bottom 40 rows
for y in range(h - 40, h):
    for x in range(int(w * 0.4), int(w * 0.8)):
        b, g, r, a = logo[y, x]
        # Check for isolated orange/red line
        if a > 0 and r > 150 and g < 100:
            logo[y, x] = [0, 0, 0, 0]

cv2.imwrite(r"frontend\public\assets\images\logo_transparent.png", logo)
cv2.imwrite(r"frontend\public\logo.png", logo)
cv2.imwrite(r"frontend\src\assets\logo.png", logo)

# Also create dark theme version and badge
badge_size = max(h, w) + 40
badge = np.zeros((badge_size, badge_size, 4), dtype=np.uint8)
oy = (badge_size - h) // 2
ox = (badge_size - w) // 2
badge[oy:oy+h, ox:ox+w] = logo

cv2.imwrite(r"frontend\public\assets\images\logo_badge.png", badge)
cv2.imwrite(r"frontend\public\favicon.png", cv2.resize(badge, (192, 192), interpolation=cv2.INTER_AREA))
print("Logo touched up and saved.")
