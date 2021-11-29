import os
import random
import socket
import string
import sys
from utils import *

port = sys.argv[1]

id_list = []

path = ""
ID = ""
data = ""
origin_cwd = os.getcwd()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12345))
server.listen(5)
while True:
    path = ""
    ID = ""

    client_socket, client_address = server.accept()
    data = client_socket.recv(1024).decode()

    # if id is not in id_list - create random one and send it.
    if data not in id_list:
        # Create a random id.
        ID = ''.join((random.choices(string.ascii_lowercase + string.digits, k=128)))
        id_list.append(ID)
        os.mkdir(ID)
        client_socket.send(ID.encode()) # Sending an acknowledgment
        os.chdir(os.path.join(origin_cwd, ID)) # Changing the current working directory
        #print(os.getcwd())
        is_dir = int(data[0])  # If the key is 0 - then it's a directory, if it's 1 then it's a file.
        path = data[1:]  # The relative directory with out the key.
        last_slash_index = path.rfind('/')

        # Checks if there is a / in the path - which means there are subdirectories.
        if last_slash_index != -1:
            # Create a relative directory 1 step before the final one.
            os.makedirs(path[:last_slash_index])
            # Changing the current working directory
            os.chdir(os.path.join(os.getcwd(), path[:last_slash_index]))

        dir_name = path[last_slash_index + 1:]
        if is_dir == 0:
            # back up the entire folder.
            recv_folder(client_socket)
        elif is_dir == 1:
            # create & backup file.
            # Removing the exisiting file
            print(os.getcwd())
            if os.path.exists(dir_name):
                os.remove(dir_name)
            recv_file(dir_name, client_socket)

    # ID is in the list - the client is already registered.
    else:
        ID = data
        client_socket.send(("ack").encode())  # Sending an acknowledgment.
        send_folder(os.path.join(os.getcwd(), ID), client_socket)

    client_socket.close()
    os.chdir(origin_cwd)
    print('Client disconnected')
