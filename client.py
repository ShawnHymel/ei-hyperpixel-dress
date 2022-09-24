"""
Main client script for the Pi Zero

Connects to Pi 4 server and waits for image data to be sent using sockets.
Scales the image as needed to fit on the HyperPixel 2" Round display using
PyGame.

Author: Shawn Hymel (Edge Impulse)
Date: September 24, 2022
License: Apache-2.0
"""

import os, time, socket, pickle, struct

import pygame
import cv2

# Settings
DEBUG = True                    # Prints debugging info to console
MIRROR = True                   # Mirror the image on the HyperPixel
ROTATION = 90                   # Rotate image (0, 90, 180, 270)
DISPLAY_RES = (480, 480)        # Resolution of HyperPixel
HOST = '192.168.7.1'            # Address of the server (Pi 4)
PORT = 8484                     # Port of server (Pi 4)
KEEPALIVE = "ACK"               # Keep alive message to send to server
SOCKET_TIMEOUT = 3.0            # Wait this no. of seconds before closing socket

def main():

    # Initialize display
    pygame.display.init()
    surface = pygame.display.set_mode(DISPLAY_RES)

    # Disable mouse
    pygame.event.set_blocked(pygame.MOUSEMOTION)
    pygame.mouse.set_visible(False)

    # Pre-calculate the payload size
    payload_size = struct.calcsize(">L")
    
    # Main client loop
    connected = False
    running = True
    while running:

        # Iterate over all received game events in the queue
        for event in pygame.event.get():

            # Check for GUI or keystroke exits
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                break

        # Try to connect if there is no connection
        if not connected:
            try:
                if DEBUG:
                    print("Connecting to " + str(HOST) + ":" + 
                            str(PORT) + "...")
                client_socket = socket.socket(socket.AF_INET, 
                                                socket.SOCK_STREAM)
                client_socket.connect((HOST, PORT))
                if DEBUG:
                    print("Connected!")
                connected = True
            except socket.error as e:
                print("Error: Could not connect to server")
                time.sleep(1.0)
                connected = False

        # Wait for message from server and respond with ack
        else:
            client_socket.settimeout(SOCKET_TIMEOUT)
            data = b""
            try:
                
                # Receive message size header
                timestamp = time.time()
                while len(data) < payload_size:
                    if time.time() - timestamp >= SOCKET_TIMEOUT:
                        raise RuntimeError("Timed out waiting for data")
                    data += client_socket.recv(4096)

                # Parse the received data
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack(">L", packed_msg_size)[0]

                # Receive payload
                timestamp = time.time()
                while len(data) < msg_size:
                    if time.time() - timestamp >= SOCKET_TIMEOUT:
                        raise RuntimeError("Timed out waiting for data")
                    data += client_socket.recv(4096)

                # Parse the payload
                frame_data = data[:msg_size]
                data = data[msg_size:]

                # Uncompress the image
                img = pickle.loads(frame_data, 
                                        fix_imports=True, 
                                        encoding='bytes')
                img = cv2.imdecode(img, cv2.IMREAD_COLOR)

                # Send keepalive message back to server
                client_socket.sendall(bytes(KEEPALIVE, 'UTF-8'))

            # Try reconnecting if we lose the connection
            except socket.timeout as e:
                print("Socket timeout:", str(e))
                connected = False
                continue
            except socket.error as e:
                print("Socket error:", str(e))
                connected = False
                continue
            except RuntimeError as e:
                print("Runtime error:", str(e))
                connected = False
                continue
            
            # Resize, rotate, and flip image if requested
            img = cv2.resize(img, DISPLAY_RES, interpolation=cv2.INTER_LINEAR)
            if ROTATION == 90:
                img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            elif ROTATION == 180:
                img = cv2.rotate(img, cv2.ROTATE_180)
            elif ROTATION == 270:
                img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOWISE)
            if not MIRROR:
                img = cv2.flip(img, 1)

            # Draw image on surface
            frame = pygame.surfarray.make_surface(img)
            surface.blit(frame, (0,0))

            # Draws the surface object to the screen
            pygame.display.update()

    # Quite and close the connection if all else fails
    client_socket.close()
    pygame.quit()

if __name__ == "__main__":
    main()