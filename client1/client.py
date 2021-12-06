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

    if command == "Move" or command == "Rename":
        s.send(event.dst_path.encode())
        wait_for_ack(s)

    # Return the socket
    return s


def on_moved(event):
    src_path = event.src_path
    dst_path = event.dst_path

    # Need to check if the event is really a move event:
    # If the source path exists:
    if os.path.exists(os.path.join(os.getcwd(), src_path)):
        socket = setup_command(event, "Move")
        return

    # If an outputstream file occurs - we  need to call on_modified, a change in a file has been made. .
    if src_path.find(".goutputstream") != -1:
        socket = setup_command(event, "Modify")
        send_file(event.src_path, socket)
        return

    # check if the event is a rename event:
    src_i = src_path.rfind("/")
    dst_i = dst_path.rfind("/")

    # The event is not move or modify
    # If the last part of the paths are not equal,
    # and the other paths are equal (till the last slash)
    if src_path[:src_i] == dst_path[:dst_i] and src_path[src_i + 1:] != dst_path[dst_i + 1:]:
        setup_command(event, "Rename")


def on_created(event):
    # Ignore outputstream files - it means a change has been made in a file.
    if event.src_path.find(".goutputstream") != -1:
        return

    socket = setup_command(event, "Create")
    # If a file has been created, the content needs to be sent by the client.
    if os.path.isfile(event.src_path):
        send_file(os.path.join(os.getcwd(), event.src_path), socket)


def on_modified(event):
    pass

    # Need to check if it is really a modify event.


def on_deleted(event):
    setup_command(event, "Delete")


def execute_commands(s):
    command = ""
    command = s.recv(BUFFER).decode()
    s.send(ACK)
    while command != "Done":
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
            src_path = path[1:dollar]  # src path starts after the type (0/1) till the slash.
            dst_path = path[dollar + 1:]  # dst path starts after the slash.
            move(src_path, dst_path)
        if command == "Modify":
            modify(s, path)
        if command == "Rename":
            # The path is divided to name and path - "name/0path"
            dollar = path.find("$")
            name = path[:dollar]
            os.rename(path[dollar + 2:], name)

        command = s.recv(BUFFER).decode()
        s.send(ACK)


origin_cwd = os.getcwd()
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((ip, 12345))

if user_id != "":
    # Sending the ID
    client_socket.send(user_id.encode())
    computer_id = client_socket.recv(10).decode()
    # Sending ack
    client_socket.send(ACK)
    # Recieving the folder.
    recv_folder(client_socket)

# If ID does not exist.
else:
    if os.path.isdir(os.path.join(os.getcwd(), directory)):
        # Key = 0 means that this directory is a folder.
        d = ("0" + directory)
        client_socket.send(d.encode())
        user_id = (client_socket.recv(1024)).decode()
        # Cutting the computer id from the total id.
        i = user_id.rfind("/")
        computer_id = user_id[i + 1:]
        user_id = user_id[:i]
        send_folder(directory, client_socket)
    elif os.path.isfile(os.path.join(os.getcwd(), directory)):
        # Key = 1 means that this directory is a folder.
        d = ("1" + directory)
        client_socket.send(d.encode())
        user_id = (client_socket.recv(1024)).decode()
        # Cutting the computer id from the total id.
        i = user_id.rfind("/")
        computer_id = user_id[i + 1:]
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

observer.schedule(event_handler, directory, recursive=True)
observer.start()

while True:
    try:
        pass
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
