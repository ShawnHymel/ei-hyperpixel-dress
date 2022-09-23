"""
Run on the Pi 4
"""

import os, sys, socket, pickle, struct, time

import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray

# Settings
HOST = ''
PORT = 8484
RES_CAPTURE = (1088, 1088)              # Resolution captured by the camera
RES_RESIZE = (320, 320)                 # Resolution expected by model
CAM_ROTATION = 90                       # Camera rotation (0, 90, 180, or 270)
JPEG_QUALITY = 90                       # JPEG quality

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print('Socket created')

s.bind((HOST,PORT))
print('Socket bind complete')
s.listen(10)
print('Socket now listening')

conn, addr = s.accept()

data = b""
payload_size = struct.calcsize(">L")
print("payload_size: {}".format(payload_size))

# Start the camera
with PiCamera() as camera:
    
    # Configure camera settings
    camera.resolution = RES_CAPTURE
    camera.rotation = CAM_ROTATION
    
    # Container for our frames
    raw_capture = PiRGBArray(camera, size=RES_CAPTURE)

    # Continuously capture frames (this is our while loop)
    for frame in camera.capture_continuous(raw_capture, 
                                            format='bgr', 
                                            use_video_port=True):

        # Get Numpy array that represents the image
        img = frame.array
        
        # Convert to RGB and resize
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, RES_RESIZE, interpolation=cv2.INTER_LINEAR)

        # Clear the stream to prepare for next frame
        raw_capture.truncate(0)

        # Compress image
        _, img_compressed = cv2.imencode('.jpg', 
                                            RES_RESIZE, 
                                            [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
        img_data = pickle.dumps(img_compressed, 0)
        size = len(img_data)
        print("Data length:", size)

        # Send to client
        conn.sendall(img_data)

        # Limit to 1 fps
        time.sleep(1.0)
