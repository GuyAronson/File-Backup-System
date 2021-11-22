import socket
import sys
import string
import random
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os


# Function to recieve a single file.
def recv_file(file_name, client_socket):
    # Open the file.
    file = open(file_name, 'wb')
    # Getting the first chunk of bytes.
    chunk = client_socket.recv(1024)
    while chunk != b'':
        # Writing the bytes while the chunk isn't empty.
        print(chunk)
        file.write(chunk)
        chunk = client_socket.recv(1024)
    file.close()


# Function to recieve a folder and its sub-directories.
def recv_folder(client_socket):
    # Saving the original working directory.
    cwd = os.getcwd()
    # First root recieve.
    data = client_socket.recv(1024).decode()
    dir_name = data
    while data:

        # Got the root path of the directory
        os.makedirs(dir_name)
        # Change working directory.
        os.chdir(dir_name)

        # Getting the first file/folder directory.
        data = client_socket.recv(1024).decode()

        # Checks if the client stopped sending info.
        if data != "":
            break

        # Extracting the key & the directory name
        is_dir = int(data[0])
        dir_name = data[1:]

        # Running while there are files in the directory.
        while is_dir == 1:
            # Getting the file.
            recv_file(dir_name, client_socket)
            # Getting the next file/folder name
            data = client_socket.recv(1024).decode()
            is_dir = data[0]
            dir_name = data[1:]
        data = dir_name
#########################################

port = sys.argv[0]

id_list = []

path = ""
ID = ""
data = ""
#is_dir = 0
origin_cwd = os.getcwd()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12345))
server.listen(5)
while True:
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
    print('Client disconnected')
