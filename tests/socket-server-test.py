"""
Run this on the Pi 4
"""

import os, socket, threading, time

# Settings
HOST = '127.0.0.1'
PORT = 8484
KEEPALIVE = "ACK"
SOCKET_TIMEOUT = 3.0            # Wait this no. of seconds before closing socket

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

        # Create socket for listening
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server_socket.bind((self.host, self.port))
        except socket.error as e:
            print("ERROR:", str(e))
        print("Socket is listening...")

        # Start listening on socket
        server_socket.listen(10)

        # Spin off new thread for each new connection
        running = True
        while running:
            client_socket, client_address = server_socket.accept()
            print("Connected to: " + client_address[0] + ":" + str(client_address[1]))
            client_thread = ClientThread(client_address, client_socket)
            client_thread.start()

# Client connection thread
class ClientThread(threading.Thread):

    # Constructor
    def __init__(self, client_address, client_socket):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.client_address = client_address

    # Thread loop
    def run(self):
        running = True
        while running:
            
            # Send message to client
            msg = "Test broadcast from server"
            num_sent = self.client_socket.send(bytes(msg, 'UTF-8'))
            print("Wrote " + str(num_sent) + " bytes to: " + str(self.client_address))

            # Wait for keepalive message response
            self.client_socket.settimeout(SOCKET_TIMEOUT)
            msg = ""
            try: 
                data = self.client_socket.recv(1024)
                msg = data.decode()
                print("From client:", data.decode())
            except socket.timeout as e:
                print("Socket timeout:", str(e))

            # If we don't get a keepalive message, shut socket down
            if msg != KEEPALIVE:
                running = False

            time.sleep(1.0)

        self.client_socket.close()
        print("Client " + str(self.client_address) + " disconnected")

#-------------------------------------------------------------------------------
# Main

def main():

    # Start listening thread
    listening_thread = ListeningThread(HOST, PORT)
    listening_thread.run()

    # Do nothing
    while True:
        time.sleep(1.0)

if __name__ == "__main__":
    main()