"""
Run on Pi 4 connected to a monitor (not HyperPixel).

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
draw_frames = True                      # Show frame and bounding boxes
capture_res = (1088, 1088)              # Resolution captured by the camera
resize_res = (320, 320)                 # Resolution expected by model
rotation = 90                            # Camera rotation (0, 90, 180, or 270)
threshold = 0.4                         # Prediction value must be over this
box_increase = 0.2                      # % to add to the size of the box
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
        
        # Redefine the bounding box: make it bigger and make it square
        bboxes = []
        for bbox in res['result']['bounding_boxes']:
            if bbox['value'] >= threshold:

                # Calculate center of bounding box
                center_x = int(bbox['x'] + (bbox['width'] / 2))
                center_y = int(bbox['y'] + (bbox['height'] / 2))

                # Find biggest dimension, make it bigger
                new_wh = max(bbox['width'], bbox['height']) * (1 + box_increase)
                new_wh = int(new_wh)

                # Clamp new dimensions
                new_x0 = int(max(center_x - (new_wh / 2), 0))
                new_y0 = int(max(center_y - (new_wh / 2), 0))
                new_x1 = int(min(new_x0 + new_wh, resize_res[0]))
                new_y1 = int(min(new_y0 + new_wh, resize_res[1]))

                # Append the new dimensions
                bboxes.append((new_wh ** 2, 
                                new_x0,
                                new_y0,
                                new_x1,
                                new_y1))
        
        # Sort bounding boxes based on areas (largest first)
        bboxes = sorted(bboxes, reverse=True)
        print("Boxes:", bboxes)

        # Create face sub-images (taken from original image)
        face_imgs = []
        face_counter = 0
        for bbox in bboxes:

            # Draw bounding box over detected object (using the resized image)
            if draw_frames:
                cv2.rectangle(img_resized,
                                (bbox[1], bbox[2]),
                                (bbox[3], bbox[4]),
                                (255, 255, 255),
                                1)

            # Scale bounding box dimensions to full image
            x0 = int((bbox[1] / resize_res[0]) * capture_res[0])
            y0 = int((bbox[2] / resize_res[1]) * capture_res[1])
            x1 = int((bbox[3] / resize_res[0]) * capture_res[0])
            y1 = int((bbox[4] / resize_res[1]) * capture_res[1])

            # Take sub-image
            face_imgs.append(img_rgb[x0:x1, y0:y1])

            # Only create a limited number of face sub-images
            face_counter += 1
            if (face_counter >= num_faces):
                break

        # Test: draw frames to screen
        if draw_frames:
            img_bgr = cv2.cvtColor(img_resized, cv2.COLOR_RGB2BGR)
            cv2.imshow("Frame", img_bgr)

        # Test: save sub-image of largest face
        for i, face_img in enumerate(face_imgs):
            img_bgr = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
            cv2.imwrite("test." + str(i) + ".jpg", img_bgr)
        
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
