"""
Run this on the Pi Zeros
"""

import socket

# Settings
HOST = '192.168.7.1'            # Address of the server (Pi 4)
PORT = 8484
KEEPALIVE = "ACK"
SOCKET_TIMEOUT = 3.0            # Wait this no. of seconds before closing socket

def main():

    # Connect to server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Main client loop
    connected = False
    while True:

        # Try to connect if there is no connection
        if not connected:
            try:
                client_socket.connect((HOST, PORT))
                connected = True
            except socket.error as e:
                print("Error: Could not connect to server")

        # Wait for message from server and respond with ack
        if connected:
            client_socket.settimeout(SOCKET_TIMEOUT)
            msg = ""
            try:
                data = client_socket.recv(1024)
                msg = data.decode()
                print("From server:", data.decode())
                client_socket.sendall(bytes(KEEPALIVE, 'UTF-8'))
            except socket.timeout as e:
                print("Socket timeout:", str(e))
                connected = False
            except socket.error as e:
                print("Socket error:", str(e))
                connected = False

    client_socket.close()


if __name__ == "__main__":
    main()