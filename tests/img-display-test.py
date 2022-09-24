"""
Display test on HyperPixel 2" Round

License: Apache-2.0
"""

import time
import cv2

# Settings
DISPLAY_RES = (480, 480)

# Define framebuffer
os.environ['SDL_FBDEV'] = "/dev/fb0"

# Load and resize image
img = cv2.imread("image.png", cv2.IMREAD_UNCHANGED)
img = cv2.resize(img, DISPLAY_RES, interpolation=INTER_LINEAR)

# Get the framebuffer
fbdev = os.getenv('SDL_FBDEV', '/dev/fb0')

# Write to framebuffer
with open(fbdev, 'wb') as fb:
    fb.write(img)

# Do nothing
while True:
    time.sleep(1.0)