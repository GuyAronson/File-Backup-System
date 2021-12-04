import socket
import sys
import os
from watchdog.observers import Observer
import watchdog.events
from watchdog.events import FileSystemEventHandler
from utils import *

port = int(sys.argv[1])
ip = sys.argv[2]
directory = sys.argv[3]
time_seconds = sys.argv[4]
user_id = ""
computer_id = '0'
if len(sys.argv) == 6:
    user_id = sys.argv[5]


def on_moved(event):
    src_path = event.src_path
    dst_path = event.dst_path
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, 12345))
    s.send("Move".encode())


def on_created(event):
    path = event.src_path
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, 12345))
    s.send("Create".encode())
    wait_for_ack(s)
    s.send((user_id+"/"+computer_id).encode())
    wait_for_ack(s)
    s.send(path.encode())
    wait_for_ack(s)

    ######### Need to check if the path is a full or realtive one - debug #############
    if os.path.isdir(path):
        send_folder(path, s)
    elif os.path.isfile(path):
        send_file(path, s)


def on_modified(event):
    path = event.src_path
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, 12345))
    s.send("Modify".encode())


def on_deleted(event):
    path = event.src_path
    full_path = os.path.join(os.getcwd(), path)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, 12345))
    s.send("Delete".encode())
    wait_for_ack(s)
    s.send((user_id+"/"+computer_id).encode())
    wait_for_ack(s)

    # Checks if the path is a folder or a file.
    if os.path.isdir(full_path):
        s.send(("0" + path).encode())
    elif os.path.isfile(full_path):
        s.send(("1" + path).encode())
    wait_for_ack(s)

    execute_commands(s)

def execute_commands(s):
    command = ""
    while command != "Done":
        command = s.recv(BUFFER).decode()
        path = s.recv(BUFFER).decode()

        # might public the create/modify/move/delete function from server to util.
        if command == "Create":
            create(s, path)
        if command == "Delete":
            delete(path)
        if command == "Move":
            move(path)
        if command == "Modify":
            modify(s, path)
        if command == "Rename":
            # The path is divided to name and path - "Rename/name/path"
            slash = path.find("/")
            name = path[:slash]
            os.rename(path[slash+1:], name)


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
    client_socket.send("ack".encode())
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

observer = Observer()
event_handler = FileSystemEventHandler()
event_handler.on_moved = on_moved
event_handler.on_created = on_created
event_handler.on_modified = on_modified
event_handler.on_deleted = on_deleted
if had_id:
    observer.schedule(event_handler, user_id, recursive=True)
else:
    observer.schedule(event_handler, directory, recursive=True)
observer.start()

while True:
    try:
        pass
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
