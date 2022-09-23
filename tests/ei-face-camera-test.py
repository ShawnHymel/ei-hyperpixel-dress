"""
https://github.com/edgeimpulse/linux-sdk-python/blob/master/examples/image/classify.py

License: Apache-2.0
"""

import os, sys, time
import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
from edge_impulse_linux.image import ImageImpulseRunner

# Settings
model_file = "mobilenet-ssd-face.eim"   # Trained ML model from Edge Impulse
capture_res = (1088, 1088)              # Resolution captured by the camera
resize_res = (320, 320)                 # Resolution expected by model
rotation = 90                            # Camera rotation (0, 90, 180, or 270)
threshold = 0.4                         # Prediction value must be over this
num_faces = 1                           # Number of faces to capture

# The ImpulseRunner module will attempt to load files relative to its location,
# so we make it load files relative to this program instead
dir_path = os.path.dirname(os.path.realpath(__file__))
model_path = os.path.join(dir_path, model_file)

# Load the model file
runner = ImageImpulseRunner(model_path)

# Initialize model (and print information if it loads)
try:
    model_info = runner.init()
    print("Model name:", model_info['project']['name'])
    print("Model owner:", model_info['project']['owner'])
    
# Exit if we cannot initialize the model
except Exception as e:
    print("ERROR: Could not initialize model")
    print("Exception:", e)
    if (runner):
            runner.stop()
    sys.exit(1)

# Initial framerate value
fps = 0

# Start the camera
with PiCamera() as camera:
    
    # Configure camera settings
    camera.resolution = capture_res
    camera.rotation = rotation
    
    # Container for our frames
    raw_capture = PiRGBArray(camera, size=capture_res)

    # Continuously capture frames (this is our while loop)
    for frame in camera.capture_continuous(raw_capture, 
                                            format='bgr', 
                                            use_video_port=True):
                                            
        # Get timestamp for calculating actual framerate
        timestamp = cv2.getTickCount()
        
        # Get Numpy array that represents the image
        img = frame.array
        
        # Convert to RGB and resize
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, resize_res, interpolation=cv2.INTER_LINEAR)
        
        # Encapsulate raw values into array for model input
        features, cropped = runner.get_features_from_image(img_resized)
        
        # Perform inference
        res = None
        try:
            res = runner.classify(features)
        except Exception as e:
            print("ERROR: Could not perform inference")
            print("Exception:", e)
            
        # Display predictions and timing data
        # print("Output:", res)
        
        # Go through each of the returned bounding boxes
        bboxes = []
        for bbox in res['result']['bounding_boxes']:
            if bbox['value'] >= threshold:
                bboxes.append((bbox['width'] * bbox['height'], 
                                bbox['x'],
                                bbox['y'],
                                bbox['width'],
                                bbox['height']))
        
        # Sort bounding boxes based on areas (largest first)
        bboxes = sorted(bboxes, reverse=True)
        print("Boxes:", bboxes)

        # Create face images (taken from original image)
        face_imgs = []
        face_counter = 0
        for bbox in bboxes:

            # Scale x, y, width, and height
            x = int(bbox[1] * capture_res[0] / resize_res[0])
            y = int(bbox[2] * capture_res[1] / resize_res[1])
            w = int(bbox[3] * capture_res[0] / resize_res[0])
            h = int(bbox[4] * capture_res[1] / resize_res[1])

            # Take sub-image
            face_imgs.append(img_rgb[x:(x + w), y:(y + h)])

            # Only create a limited number of face sub-images
            face_counter += 1
            if (face_counter >= num_faces):
                break

        # if len(face_imgs) > 0:
        #     cv2.imwrite("test.jpg", face_imgs[0])
        
        # Clear the stream to prepare for next frame
        raw_capture.truncate(0)

        # Calculate framrate
        frame_time = (cv2.getTickCount() - timestamp) / cv2.getTickFrequency()
        fps = 1 / frame_time
        print("FPS:", fps)
        
        # Press 'q' to quit
        if cv2.waitKey(1) == ord('q'):
            break
        
# Clean up
cv2.destroyAllWindows()
