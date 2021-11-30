import socket
import sys
import string
import random
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os
from utils import *

port = int(sys.argv[1])
ip = sys.argv[2]
directory = sys.argv[3]
time_seconds = sys.argv[4]
ID = ""
if len(sys.argv) == 6:
    ID = sys.argv[5]

origin_cwd = os.getcwd()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((ip, 12345))

if ID != "":
    # Sending the ID
    client_socket.send(ID.encode())
    # Waiting for ack
    wait_for_ack(client_socket)
    # Recieving the folder.
    recv_folder(client_socket)
    # Getting back the start directory.
    os.chdir(origin_cwd)

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



