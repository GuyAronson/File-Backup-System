import socket
import sys
import os
from watchdog.observers import Observer
import watchdog.events
from watchdog.events import FileSystemEventHandler
from utils import *


ip = "127.0.0.1"
directory = "c"
time_seconds = 2
user_id = ""
computer_id = ""


origin_cwd = os.getcwd()
had_id = False
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((ip, 12346))

if user_id != "":
    had_id = True
    # Sending the ID
    client_socket.send(user_id.encode())
    computer_id = client_socket.recv(10)
    # Sending ack
    client_socket.send(ACK)
    # Recieving the folder.
    recv_folder(client_socket)

# If ID does not exist.
else:
    had_id = False
    if os.path.isdir(os.path.join(os.getcwd(), directory)):
        # Key = 0 means that this directory is a folder.
        d = ("0" + directory)
        client_socket.send(d.encode())
        user_id = (client_socket.recv(1024)).decode()
        # Cutting the computer id from the total id.
        i = user_id.rfind("/")
        computer_id = user_id[i+1:]
        user_id = user_id[:i]
        send_folder(directory, client_socket)
    elif os.path.isfile(os.path.join(os.getcwd(), directory)):
        # Key = 1 means that this directory is a folder.
        d = ("1" + directory)
        client_socket.send(d.encode())
        user_id = (client_socket.recv(1024)).decode()
        # Cutting the computer id from the total id.
        i = user_id.rfind("/")
        computer_id = user_id[i+1:]
        user_id = user_id[:i]
        send_file(directory, client_socket)

# Getting back the start directory.
os.chdir(origin_cwd)
client_socket.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ip, 12346))

s.send("Modify".encode())
wait_for_ack(s)
s.send((user_id + "/" + computer_id).encode())
wait_for_ack(s)
dir = "1c/a.txt"
s.send(dir.encode())
wait_for_ack(s)
a = s.recv(4).decode()
if a == "Done":
    print("Good Done")

send_file(os.path.join(os.getcwd(), dir[1:]), s)

#send_file(os.path.join(os.getcwd(), dir[1:]), s)

