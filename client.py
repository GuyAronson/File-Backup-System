import socket
import sys
import string
import random
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os


def send_file(directory, s):
    file = open(directory, "rb")
    chunk = file.read(1024)
    while chunk:
        s.send(chunk)
        chunk = file.read(1024)


def send_folder(dir, s):
    files = ""
    file_cwd = ""
    os.chdir(os.getcwd() + "/" + dir)
    for (root, dirs, files) in os.walk(dir, topdown=True):
        # Sending the root directory.
        s.send(bytes(root))

        # Changing to the current directory.
        root_cwd = dir
        first_slash = root.findfirstindex('/')
        if first_slash != -1:
            root_cwd += root[first_slash+1:]
        # Sending the files.
        for file in files:
            file_cwd = root_cwd + "/" + file
            send_file(file_cwd, s)


port = sys.argv[0]
ip = sys.argv[1]
directory = sys.argv[2]
time_seconds = sys.argv[3]
ID = ""
if len(sys.argv) == 5:
    ID = sys.argv[4]

# todo- The client will send a 1 or 0 as a key - to know whether is it a file or a directory to back up on the server.
# after registaration in the server - the client will monitor the files - using watchdog
# When a change has been made - the client will send a request for backup to the server.

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect((ip, port))

if ID != "":
    client_socket.send(bytes(ID))
    x = client_socket.recv(1024)
    if ID != x:  # Throw exception.
        pass
    client_socket.send(bytes(directory))
else:
    client_socket.send(bytes(directory))
    ID = client_socket.recv(1024)

# Check if the directory is a file or a folder.
if os.path.isdir(directory):
    # Key = 0 means that this directory is a folder.
    d = ("0" + directory)
    client_socket.send(bytes(d))
    send_folder()
elif os.path.isfile(directory):
    # Key = 1 means that this directory is a folder.
    d = ("1" + directory)
    client_socket.send(bytes(d))
    send_file(directory, client_socket)
