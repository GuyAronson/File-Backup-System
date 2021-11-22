import socket
import sys
import string
import random
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os


def send_file(directory, s):
    file = open(directory, 'rb')
    chunk = file.read(1024)
    while chunk:
        s.send(chunk)
        chunk = file.read(1024)
    s.send(b'')
    file.close()


def send_folder(directory, s):
    relative_directory = ""
    # Saving the start index of the relative directory
    start_relative_index = len(os.getcwd())+1
    last_slash = directory.rindex("/")
    if last_slash != -1:
        # Getting the realtive directory starting from the first folder to save.
        relative_directory = directory[:last_slash]
        # Changing directory to the realtive directory.
        os.chdir(os.getcwd() + "/" + relative_directory)
    #current_dir = os.getcwd()
    for (root, dirs, files) in os.walk(os.getcwd(), topdown=True):
        # Sending the root directory.
        root_last_slash = root.rindex('/')
        print(root[start_relative_index : root_last_slash])
        s.send(root[start_relative_index : root_last_slash].encode())

        # Changing to the current directory.
        #root_cwd = current_dir
        #root_last_index = root.rindex('/')
        #if root_last_index != -1:
        #    root_cwd += root[:root_last_index]
        #root_cwd = os.getcwd()
        # Sending the files.
        for file in files:
            file_cwd = root + "/" + file
            print(file_cwd)
            send_file(file_cwd, s)


port = int(sys.argv[1])
ip = sys.argv[2]
directory = sys.argv[3]
time_seconds = sys.argv[4]
ID = ""
if len(sys.argv) == 6:
    ID = sys.argv[5]

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect((ip, port))

if ID != "":
    client_socket.send(ID.encode())
    x = (client_socket.recv(1024)).decode()
    if ID != x:  # Throw exception.
        pass

    # Check if the directory is a file or a folder.
    if os.path.isdir(directory):
        # Key = 0 means that this directory is a folder.
        d = ("0" + directory)
        client_socket.send(d.encode())
        send_folder(directory, client_socket)
    elif os.path.isfile(directory):
        # Key = 1 means that this directory is a folder.
        d = ("1" + directory)
        client_socket.send(d.encode())
        send_file(directory, client_socket)

# If ID does not exist.
else:
    if os.path.isdir(directory):
        # Key = 0 means that this directory is a folder.
        d = ("0" + directory)
        client_socket.send(d.encode())
        ID = (client_socket.recv(1024)).decode()
        send_folder(directory, client_socket)
    elif os.path.isfile(directory):
        # Key = 1 means that this directory is a folder.
        d = ("1" + directory)
        client_socket.send(d.encode())
        ID = (client_socket.recv(1024)).decode()
        send_file(directory, client_socket)



