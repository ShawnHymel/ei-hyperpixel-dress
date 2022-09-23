"""
Run on the Pi Zero
"""

import socket, pickle, struct

import cv2

# Settings
HOST = '192.168.7.1'
PORT = 8484

# Connect to server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
connection = client_socket.makefile('wb')

# Continuously accept image data from server
data = b""
payload_size = struct.calcsize(">L")
print("payload_size: {}".format(payload_size))
while True:

    # Receive data
    while len(data) < payload_size:
        print("Recv:", len(data))
        data += client_socket.recv(4096)
    print("Done recv:", len(data))

    # Parse payload size
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]
    print("Message size:", msg_size)

    # Construct data from stream
    while len(data) < msg_size:
        data += client_socket.recv(4096)
    frame_data = data[:msg_size]
    data = data[msg_size:]

    # Unpickle the data
    img = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
    img = cv2.imdecode(frame, cv2.IMREAD_COLOR)

    # Save the image
    cv2.imwrite("test.jpg", img)
