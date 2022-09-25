"""
Main server script for the Pi 4

Handles incoming client connections from the Pi Zeros. Takes images with
attached Pi cam, performs face detection, and sends out the sub-images to each
of the connected Pi Zeros.

NOTE: You must update the HOSTS setting to reflect the Pi Zero interfaces.

Author: Shawn Hymel (Edge Impulse)
Date: September 23, 2022
License: Apache-2.0
"""

import os, socket, threading, time, queue, random, pickle, struct

import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
from edge_impulse_linux.image import ImageImpulseRunner

# Debug setting
DEBUG = True                            # Prints debugging info to console

# Face detection settings
model_file = "mobilenet-ssd-face.eim"   # Trained ML model from Edge Impulse
draw_frames = True                      # Show frame and bounding boxes
capture_res = (1088, 1088)              # Resolution captured by the camera
resize_res = (320, 320)                 # Resolution expected by model
default_sub_res = (240, 240)            # Default sub-image size (center of img)
rotation = 90                           # Camera rotation (0, 90, 180, or 270)
threshold = 0.4                         # Prediction value must be over this
box_increase = 0.2                      # % to add to the size of the box
num_faces = 1                           # Number of faces to capture

# Network settings
HOSTS = ['192.168.2.1', '192.168.3.1']  # Available IP addresses
PORT = 8484                     # Port of server (Pi 4)
KEEPALIVE = "ACK"               # Keep alive message to send to server
SOCKET_TIMEOUT = 3.0            # Wait this no. of seconds before closing socket

# Global client list and mutex
clients = []
clients_mutex = threading.Lock()

#-------------------------------------------------------------------------------
# Classes

# Server listening thread
class ListeningThread(threading.Thread):

    # Constructor
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port

    # Thread loop
    def run(self):

        # Create a socket for listening
        bound = False
        while not bound:
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((self.host, self.port))
                bound = True
            except socket.error as e:
                print("ERROR:", str(e))
                time.sleep(2.0)
                bound = False

        # Start listening on socket
        if DEBUG:
            print("Socket is listening...")
        server_socket.listen(10)

        # Spin off new thread for each new connection
        running = True
        while running:
            client_socket, client_address = server_socket.accept()
            client_full_address = str(client_address[0]) + ":" + str(client_address[1])
            if DEBUG:
                print("Connected to: " + client_full_address)
            client_thread = ClientThread(client_address, client_socket)
            client_thread.start()

            # Add client to list
            clients_mutex.acquire()
            clients.append(client_thread)
            clients_mutex.release()

# Client connection thread
class ClientThread(threading.Thread):

    # Constructor
    def __init__(self, client_address, client_socket):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.client_address = client_address
        self.q = queue.Queue()

    # Thread loop
    def run(self):
        running = True
        while running:
            
            # Send message to client
            data = self.q.get()
            num_sent = self.client_socket.sendall(data)
            if DEBUG:
                print("Sent data to: " + str(self.client_address))

            # Wait for keepalive message response
            self.client_socket.settimeout(SOCKET_TIMEOUT)
            msg = ""
            try: 
                data = self.client_socket.recv(1024)
                msg = data.decode()
                if DEBUG:
                    print("From client:", data.decode())
            except socket.timeout as e:
                print("Socket timeout:", str(e))
            except socket.error as e:
                print("Socket error:", str(e))

            # If we don't get a keepalive message, shut socket down
            if msg != KEEPALIVE:
                running = False

        # Close socket
        self.client_socket.close()
        if DEBUG:
            print("Client " + str(self.client_address) + " disconnected")

        # Remove self from list
        clients_mutex.acquire()
        clients.remove(self)
        clients_mutex.release()

    # Add message to queue
    def send(self, data):
        self.q.put(data)

#-------------------------------------------------------------------------------
# Main

def main():

    # The ImpulseRunner module will attempt to load files relative to its location,
    # so we make it load files relative to this program instead
    dir_path = os.path.dirname(os.path.realpath(__file__))
    model_path = os.path.join(dir_path, model_file)

    # Load the model file
    runner = ImageImpulseRunner(model_path)

    # Initialize model (and print information if it loads)
    try:
        model_info = runner.init()
        if DEBUG:
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

    # Start listening thread
    for host in HOSTS:
        listening_thread = ListeningThread(host, PORT)
        listening_thread.start()

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
            if DEBUG:
                print("Boxes:", bboxes)

            # Create face sub-images (taken from original image)
            face_imgs = []
            face_counter = 0
            for bbox in bboxes:

                # Scale bounding box dimensions to full image
                x0 = int((bbox[1] / resize_res[0]) * capture_res[0])
                y0 = int((bbox[2] / resize_res[1]) * capture_res[1])
                x1 = int((bbox[3] / resize_res[0]) * capture_res[0])
                y1 = int((bbox[4] / resize_res[1]) * capture_res[1])

                # Take sub-image
                face_imgs.append(img_rgb[x0:x1, y0:y1])

                # Limit number of faces to number of connected clients
                face_counter += 1
                if (face_counter >= len(clients)):
                    break

            # Compress and send image data to clients
            for i, client in enumerate(clients):

                # Send sub-image in bounding box or default to center of image
                if i < len(bboxes):
                    sub_img = face_imgs[i]
                else:
                    center_x = capture_res[0] / 2
                    center_y = capture_res[1] / 2
                    x0 = int(center_x - (default_sub_res[0] / 2))
                    y0 = int(center_y - (default_sub_res[1] / 2))
                    x1 = int(center_x + (default_sub_res[0] / 2))
                    y1 = int(center_y + (default_sub_res[1] / 2))
                    sub_img = img_rgb[x0:x1, y0:y1]
                
                # Transmit sub-image to connected client
                try:
                    _, img_jpg = cv2.imencode('.jpg', sub_img)
                    data = pickle.dumps(img_jpg, 0)
                    size = len(data)
                    client.send(struct.pack(">L", size) + data)
                    if DEBUG:
                        print("Sending image of size " + str(sub_img.shape) + \
                                " to " + str(client.client_address))
                except Exception as e:
                    print("Error:", str(e))
                    continue
            
            # Clear the stream to prepare for next frame
            raw_capture.truncate(0)

            # Calculate framrate
            frame_time = (cv2.getTickCount() - timestamp) / cv2.getTickFrequency()
            fps = 1 / frame_time
            if DEBUG:
                print("FPS:", fps)
            
            # Press 'q' to quit
            if cv2.waitKey(1) == ord('q'):
                break
            
    # Clean up
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()