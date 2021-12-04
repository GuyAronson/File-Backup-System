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
computer_id = ""
if len(sys.argv) == 6:
    user_id = sys.argv[5]

def setup_command(event, command):
    # The relative source path
    path = event.src_path
    # Create the full source path
    full_path = os.path.join(os.getcwd(), path)

    # Create a socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, 12345))

    # Sending the command to the server.
    s.send(command.encode())
    wait_for_ack(s)

    # Sending the user and computer ids.
    s.send((user_id + "/" + computer_id).encode())
    wait_for_ack(s)

    # Checks if the path is a folder or a file - the sending
    if os.path.isdir(full_path):
        s.send(("0" + path).encode())
    elif os.path.isfile(full_path):
        s.send(("1" + path).encode())
    wait_for_ack(s)

    # Execute the commands waiting in the server for the client's computer.
    execute_commands(s)

    if command == "Move":
        s.send(event.dst_path.encode())
        wait_for_ack(s)

    # Return the socket
    return s


def on_moved(event):
    socket = setup_command(event, "Move")

    # Need to check if the event is really a move event.

    # Need to check if the event is actually a rename event.

    # Need to send the new name if the command is Rename

    # If an outputstream file occurs - we  need to call on_modified, a change in a file has been made. .


def on_created(event):
    path = event.src_path
    full_path = os.path.join(os.getcwd(), path)
    if os.path.isfile(full_path):
        is_dir = 1
    else:
        is_dir = 0

    socket = setup_command(event, "Create")

    if is_dir == 1:
        send_file(full_path, socket)
        
    # Ignore outputstream files - it means a change has been made in a file.

def on_modified(event):
    socket = setup_command(event, "Modify")

    # After the set up - we need to send the file that has been modified.
    send_file(os.path.join(os.getcwd(), event.src_path), socket)


    # Need to check if it is really a modify event.
    # Ignore outputstream files - it means a change has been made in a file.

def on_deleted(event):
    socket = setup_command(event, "Delete")

def execute_commands(s):
    command = ""
    while command != "Done":
        command = s.recv(BUFFER).decode()
        s.send(ACK)
        # The path is relative.
        path = s.recv(BUFFER).decode()
        s.send(ACK)
        # might public the create/modify/move/delete function from server to util.
        if command == "Create":
            create(s, path)
        if command == "Delete":
            is_dir = int(path[0])
            path = path[1:]
            # This recursive function will delete every file/sub-folder in this path.
            delete(path)

            # Eventually delete the folder since it's empty.
            if is_dir == 0:
                os.rmdir(os.path.join(os.getcwd(), path))

        if command == "Move":
            # path = "0src_path/dst_path"
            dollar = path.find("$")
            src_path = path[1:dollar]    # src path starts after the type (0/1) till the slash.
            dst_path = path[dollar + 1:] # dst path starts after the slash.
            move(src_path, dst_path)
        if command == "Modify":
            modify(s, path)
        if command == "Rename":
            # The path is divided to name and path - "name/0path"
            dollar = path.find("$")
            name = path[:dollar]
            os.rename(path[dollar+2:], name)


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
