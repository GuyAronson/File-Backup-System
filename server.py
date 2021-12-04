import os
import random
import socket
import string
import sys
from utils import *

def execute_commands(s, usr_id, cmp_id):
    # List of updates for the computer.
    updates = users[usr_id][cmp_id]

    # Checks the updates list.
    if len(updates) != 0:
        # Looping over the updates.
        for update in updates:
            i = update.find("$")
            command = update[:i]
            _path = update[i + 1:]
            # Send the command name
            s.send(command.encode())
            wait_for_ack(s)
            # Send the path to create - ## the first byte is the path's type##
            s.send(_path.encode())
            wait_for_ack(s)
            if command == "Create" or command == "Modify":
                # Send the folder/file
                is_dir = int(_path[0])
                if is_dir == 1:
                    send_file(_path[1:], s)
            # If command is "Move" - the client needs to seperate the paths ###

            # Might need to send ack after every update. ####
            # Remove the update (the update has been done)
            users[usr_id][cmp_id].remove(update)

    # All updates have been sent, the client can stop.
    s.send("Done".encode())

def check_for_updates(update, s):
    command_text = update

    # Ack for receiving the update
    s.send(ACK)

    # Get the ids:
    data = s.recv(BUFFER).decode()
    s.send(ACK)
    i = data.rfind("/")
    user_id = data[:i]
    computer_id = data[i + 1:]

    # Getting the path - the first byte is the dir's type.
    path = s.recv(BUFFER).decode()
    s.send(ACK)

    command_text = command_text + "$" + path

    # Changing the path to be realtive for the server with the type:
    is_dir = path[0]
    path = os.path.join(user_id, path[1:])
    path = is_dir + path

    # Execute commands waiting in the buffer
    execute_commands(s, user_id, computer_id)

    if update == "Create":
        create(s, path)

    if update == "Move":
        # Deleting the type - irrelevant.
        path = path[1:]

        # Get the destination path as well
        dst_path = s.recv(BUFFER).decode()
        s.send(ACK)
        # Changing the dst path to be relative to server.
        new_dst_path = os.path.join(user_id, dst_path)

        move(path, new_dst_path)

        # Add it to the command text
        command_text = command_text + "$" + dst_path

    if update == "Modify":
        modify(s, path)

    if update == "Delete":
        is_dir = int(path[0])
        path = path[1:]
        # This recursive function will delete every file/sub-folder in this path.
        delete(path)

        # Eventually delete the folder since it's empty.
        if is_dir == 0:
            os.rmdir(os.path.join(os.getcwd(), path))

    if update == "Rename":
        # Getting the new name:
        name = s.recv(BUFFER).decode()
        s.send(ACK)

        # Renaming the file/folder.
        os.rename(path, name)

    # Pushing the update to all computers:
    for computer in users[user_id].keys():
        if computer != computer_id:
            users[user_id][computer].append(command_text)


port = sys.argv[1]
# Dictionary - its key is the id and the value is another dict of computers & list of commands.
users = {}

path = ""
user_id = ""
data = ""
origin_cwd = os.getcwd()
commands = ["Create", "Move", "Modify", "Delete", "Rename"]

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12345))
server.listen(5)
while True:
    path = ""
    user_id = ""

    client_socket, client_address = server.accept()
    data = client_socket.recv(BUFFER).decode()

    # For monitored Clients
    if data in commands:
        check_for_updates(data, client_socket)

    # For first connection from a client - received an id or a directory to back up.
    else:
        user_id_list = users.keys()
        # if id is not in id_list - create random one and send it.
        if data not in user_id_list:
            # Create a random id.
            user_id = ''.join((random.choices(string.ascii_lowercase + string.digits, k=128)))
            # Creating new dict for the specific user ID
            users[user_id] = {}
            # This is the first computer - the id is 1
            computer_id = '1'
            # Creating new dict for the  commands - commands[0]=modify commands, commands[1]= the rest commands.
            users[user_id][computer_id] = []
            # Create the folder with the ID
            os.mkdir(user_id)
            # Sending an acknowledgment with the user_id and the computer_id
            client_socket.send((user_id + "/" + computer_id).encode())
            os.chdir(os.path.join(origin_cwd, user_id))  # Changing the current working directory
            # print(os.getcwd())
            is_dir = int(data[0])  # If the key is 0 - then it's a directory, if it's 1 then it's a file.
            path = data[1:]  # The relative directory with out the key.
            last_slash_index = path.rfind('/')

            # Checks if there is a / in the path - which means there are subdirectories.
            if last_slash_index != -1:
                # Create a relative directory 1 step before the final one.
                os.makedirs(path[:last_slash_index])
                # Changing the current working directory
                os.chdir(os.path.join(os.getcwd(), path[:last_slash_index]))

            dir_name = path[last_slash_index + 1:]
            if is_dir == 0:
                # back up the entire folder.
                recv_folder(client_socket)
            elif is_dir == 1:
                # create & backup file.
                # Removing the existing file
                print(os.getcwd())
                if os.path.exists(dir_name):
                    os.remove(dir_name)
                recv_file(dir_name, client_socket)

        # ID is in the list - the client is already registered.
        else:
            user_id = data
            # Get the computers id list, set the id of the new computer to length + 1.
            computer_id = str(len(users[user_id].keys()) + 1)
            # Creating new dict for the  commands - commands[0]=modify commands, commands[1]= the rest commands.
            users[data][computer_id] = []
            client_socket.send(computer_id.encode())  # Sending an acknowledgment.
            # Waiting for ack
            wait_for_ack(client_socket)
            send_folder(os.path.join(os.getcwd(), user_id), client_socket)

    client_socket.close()
    os.chdir(origin_cwd)
    print('Client disconnected')
