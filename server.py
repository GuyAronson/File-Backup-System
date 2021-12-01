import os
import random
import socket
import string
import sys
from utils import *

def create(s):
    data = s.recv(1024)
    s.send("ack".encode())
    i = data.rfind("/")
    user_id = data[:i]
    computer_id = data[i+1:]
    updates = users[user_id][computer_id]


def check_for_updates(update, s):
    s.send("ack".encode())
    if update == "Create":
        create(s)
    if update == "Move":
        pass
    if update == "Modify":
        pass
    if update == "Delete":
        pass

port = sys.argv[1]
# Dictionary - its key is the id and the value is another dict of computers & list of commands.
users = {}

path = ""
user_id = ""
data = ""
origin_cwd = os.getcwd()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12345))
server.listen(5)
while True:
    path = ""
    user_id = ""

    client_socket, client_address = server.accept()
    data = client_socket.recv(1024).decode()

    # For monitored Clients
    check_for_updates(data,client_socket)

    user_id_list = users.keys()
    # if id is not in id_list - create random one and send it.
    if data not in user_id_list:
        # Create a random id.
        user_id = ''.join((random.choices(string.ascii_lowercase + string.digits, k=128)))
        # Creating new dict for the specific user ID
        users[data] = {}
        # This is the first computer - the id is 1
        computer_id = '1'
        # Creating new dict for the computer_id and the commands.
        users[data][computer_id] = []
        # Create the folder with the ID
        os.mkdir(user_id)
        # Sending an acknowledgment with the user_id and the computer_id
        client_socket.send((user_id + "/" + computer_id).encode())
        os.chdir(os.path.join(origin_cwd, user_id)) # Changing the current working directory
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
            # Removing the existing file
            print(os.getcwd())
            if os.path.exists(dir_name):
                os.remove(dir_name)
            recv_file(dir_name, client_socket)

    # ID is in the list - the client is already registered.
    else:
        user_id = data
        # Get the computers id list, set the id of the new computer to length + 1.
        computer_id = str(len(users[data].keys()) + 1)
        # Creating new dict for the computer_id and the commands.
        users[data][computer_id] = []
        client_socket.send(computer_id.encode())  # Sending an acknowledgment.
        # Waiting for ack
        wait_for_ack(client_socket)
        send_folder(os.path.join(os.getcwd(), user_id), client_socket)

    client_socket.close()
    os.chdir(origin_cwd)
    print('Client disconnected')
