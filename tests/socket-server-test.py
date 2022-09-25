"""
Run this on the Pi 4
"""

import os, socket, threading, time, queue, random

# Settings
HOST = '192.168.2.1'            # Address of the server (Pi 4)
PORT = 8484
KEEPALIVE = "ACK"
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
            client_full_address = str(client_address[0]) + ":" + str(client_address[1])
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
            msg = str(self.q.get())
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
            except socket.error as e:
                print("Socket error:", str(e))

            # If we don't get a keepalive message, shut socket down
            if msg != KEEPALIVE:
                running = False

        # Close socket
        self.client_socket.close()
        print("Client " + str(self.client_address) + " disconnected")

        # Remove self from list
        clients_mutex.acquire()
        clients.remove(self)
        clients_mutex.release()

    # Add message to queue
    def send(self, msg):
        self.q.put(msg)

#-------------------------------------------------------------------------------
# Main

def main():

    # Start listening thread
    listening_thread = ListeningThread(HOST, PORT)
    listening_thread.start()

    # Send out messages every second
    while True:
        
        # Generate some random numbers and sort
        rand_list = random.sample(range(0, 100), len(clients))
        rand_list = sorted(rand_list, reverse=True)
        print("Sending to clients:", rand_list)

        # Send values to clients (highest number to first in list)
        for i, client in enumerate(clients):
            client.send(rand_list[i])

        # Wait before sending again
        time.sleep(1.0)

if __name__ == "__main__":
    main()