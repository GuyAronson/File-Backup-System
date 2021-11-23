import socket
import sys
import string
import random
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os


# Function to recieve a single file.
def recv_file(file_dir, client_socket):
    file_size = int.from_bytes(client_socket.recv(8), 'big')
    # Open the file.
    file = open(file_dir, 'wb')
    # Getting the first chunk of bytes.
    data = client_socket.recv(file_size)
    file.write(data)
    # while chunk != b'':
    #     # Writing the bytes while the chunk isn't empty.
    #     print(chunk)
    #     file.write(chunk)
    #     chunk = client_socket.recv(1024)
    file.close()


# Function to recieve a folder and its sub-directories.
############### Change the recieve bytes ###################
def recv_folder(client_socket):
    # Saving the original working directory.
    cwd = os.getcwd()   # in A/
    # First, recieve relative root directory .
    data = client_socket.recv(1024).decode()
    client_socket.send(("ack").encode())
    dir_name = cwd +"/"+ data[1:]
    while data != "":
        # dir_name = dir_name.rstrip()
        # dir_name = dir_name.lstrip()
        # Got the full root's path
        os.makedirs(dir_name)
        # Change working directory to the full root's path
        os.chdir(dir_name)

        # Getting the first file/folder relative directory.
        data = client_socket.recv(1024).decode()
        client_socket.send(("ack").encode())
        data = data.rstrip()
        data = data.lstrip()
        # Checks if the client stopped sending info.
        if data == "":
            break

        # Extracting the key & the directory name
        is_dir = int(data[0])
        dir_name = cwd +"/"+ data[1:]

        # Running while there are files in the directory.
        while is_dir == 1:
            # Getting the file.
            recv_file(dir_name, client_socket)
            # Getting the next file/folder realtive directory
            data = client_socket.recv(1024).decode()
            if data != "":
                client_socket.send(("ack").encode())
                is_dir = int(data[0])
                dir_name = cwd + "/" + data[1:]
            else:
                is_dir = 0
#########################################

port = sys.argv[0]

id_list = []

path = ""
ID = ""
data = ""
origin_cwd = os.getcwd()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12346))
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
        client_socket.send(ID.encode()) # Sending an acknowledgment - ***may move to another location***
    # Id is in the list - the client is already registered.
    else:
        ID = data
        client_socket.send(ID.encode())  # Sending an acknowledgment.
        data = client_socket.recv(1024).decode()         # The data now should be the directory to backup

    os.chdir(origin_cwd + "/" + ID)    # Changing the current working directory
    print(os.getcwd())

    is_dir = int(data[0])  # If the key is 0 - then it's a directory, if it's 1 then it's a file.
    path = data[1:]    # The relative directory with out the key.

    last_slash_index = path.rfind('/')

    # Checks if there is a / in the path - which means there are subdirectories.
    if last_slash_index != -1:
        # Create a relative directory 1 step before the final one.
        os.makedirs(path[:last_slash_index])
        # Changing the current working directory
        os.chdir(os.getcwd() + "/" + path[:last_slash_index])

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

    
    client_socket.close()
    os.chdir(origin_cwd)
    print('Client disconnected')
