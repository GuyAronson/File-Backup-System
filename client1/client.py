import socket
import sys
import os
from watchdog.observers import Observer
import watchdog.events
import time
from watchdog.events import FileSystemEventHandler
from utils import *

NULL = 0
port = int(sys.argv[1])
ip = sys.argv[2]
directory = sys.argv[3]
time_seconds = sys.argv[4]
user_id = ""
computer_id = ""
updates_to_ignore = []
if len(sys.argv) == 6:
    user_id = sys.argv[5]


def setup_command(event, command):
    # the src path is outputstream, so we need the dst path.
    if command == "Modify":
        path = event.dest_path
    else:
        # The relative source path
        path = event.src_path

    if (command + "$" + path) in updates_to_ignore:
        # Deleting the update.
        updates_to_ignore.remove((command + "$" + path))
        return NULL
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
    if command == "Modify" or command == "Create":
        if os.path.isdir(full_path):
            s.send(("0" + path).encode())
        elif os.path.isfile(full_path):
            s.send(("1" + path).encode())
    else:
        s.send(path.encode())
    wait_for_ack(s)

    # Execute the commands waiting in the server for the client's computer.
    execute_commands(s)

    if command == "Move" or command == "Rename":
        s.send(event.dest_path.encode())
        wait_for_ack(s)

    # Return the socket
    return s


def on_moved(event):
    src_path = event.src_path
    dst_path = event.dest_path

    # Need to check if the event is really a move event:
    # If the source path exists:
    if os.path.exists(os.path.join(os.getcwd(), src_path)):
        socket = setup_command(event, "Move")
        return

    # If an outputstream file occurs - we  need to call on_modified, a change in a file has been made. .
    if src_path.find(".goutputstream") != -1:
        socket = setup_command(event, "Modify")
        if socket == 0:
            return
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
    if socket != 0 and os.path.isfile(event.src_path):
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
            # Adding an update to ignore when the watchdog monitor it - without the first byte of the type.
            updates_to_ignore.append(command + "$" + path[1:])
            create(s, path)

        elif command == "Delete":
            # Adding an update to ignore when the watchdog monitor it.
            updates_to_ignore.append(command + "$" + path)
            # This recursive function will delete every file/sub-folder in this path.
            delete(path)

            # Eventually delete the folder since it's empty.
            if os.path.isdir(os.path.join(os.getcwd(), path)):
                os.rmdir(os.path.join(os.getcwd(), path))

        elif command == "Move":
            # Adding an update to ignore when the watchdog monitor it.
            updates_to_ignore.append(command + "$" + path)

            dollar = path.find("$")
            src_path = path[:dollar]  # src path starts after the type (0/1) till the slash.
            dst_path = path[dollar + 1:]  # dst path starts after the slash.
            move(src_path, dst_path)

        elif command == "Modify":
            # Adding an update to ignore when the watchdog monitor it - without the first byte of the type.
            updates_to_ignore.append(command + "$" + path[1:])
            modify(s, path)

        elif command == "Rename":
            # Adding an update to ignore when the watchdog monitor it.
            updates_to_ignore.append(command + "$" + path)

            # The path is divided to name and path - "name$path"
            dollar = path.find("$")
            name_path = path[:dollar]
            os.rename(path[dollar + 1:], name_path)

        # Next command.
        command = s.recv(BUFFER).decode()
        s.send(ACK)


origin_cwd = os.getcwd()
had_id = False
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((ip, 12345))

if user_id != "":
    had_id = True
    # Sending the ID
    client_socket.send(user_id.encode())
    computer_id = client_socket.recv(10).decode()
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
time_start = time.time()
time_end = time.time()
while True:
    try:
        if time_end - time_start == time_seconds:
            # In this function we will ask an update from the server.
            # And will initiate the time_start again.
            request_an_update()

        time_end = time.time()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
