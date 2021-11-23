import socket
import sys
import string
import random
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os

def wait_for_ack(s):
    data = "0"
    while data != "ack":
        data = s.recv(3).decode()


def send_file(directory, s):
    # Get the file size in bytes
    file_size = os.path.getsize(directory)
    # Send the size of the file to the server
    bytes = file_size.to_bytes(8, 'big')
    s.send(bytes)
    # Open & read the file
    file = open(directory, 'rb')
    data = file.read(file_size)
    # Send all.
    s.sendall(data)
    # while chunk:
    #     s.send(chunk)
    #     chunk = file.read(1024)
    # s.send(b'')
    file.close()


def send_folder(directory, s):
    # Saving the start index of the relative directory
    start_relative_index =0
    cwd = os.getcwd()
    last_slash = directory.rindex("/")
    if last_slash != -1:
        # Changing directory to the realtive directory.
        os.chdir(os.getcwd() + "/" + directory)
        cwd = os.getcwd()
        start_relative_index = len(cwd)-1 # start from B
    for (root, dirs, files) in os.walk(os.getcwd(), topdown=True):
        # Sending the root directory.
        a = ("0"+root[start_relative_index:])
        s.send(a.encode())
        wait_for_ack(s)

        # Sending the files.
        for file in files:
            relative_file_cwd = root[start_relative_index:] + "/" + file
            file_cwd = root + "/" + file
            # Sending the relative file directory to the server.
            s.send(("1" + relative_file_cwd).encode())
            print(file_cwd)
            wait_for_ack(s)
            send_file(file_cwd, s)


port = int(sys.argv[1])
ip = sys.argv[2]
directory = sys.argv[3]
time_seconds = sys.argv[4]
ID = ""
if len(sys.argv) == 6:
    ID = sys.argv[5]

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect((ip, 12346))

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



