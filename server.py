import os
import random
import socket
import string
import sys
from utils import *


def create(s, path):
    # if is_dir = 0 , it;s a directory, if is_dir =1 it's a file.
    is_dir = path[0]
    # The relative directory.
    directory = path[1:]
    if is_dir == 1:
        recv_file(directory, s)
    elif is_dir == 0:
        # path is a relative directory - start from the ID folder
        # todo - Need to make sure the server current working directory (cwd) is in the ID folder.
        os.mkdir(os.path.join(os.getcwd(), path))


def modify(s, path):
    send_file(path, s)


def delete(path):
    # path is a relative path.
    full_path = os.path.join(os.getcwd(), path)
    list_dirs = os.listdir(full_path)
    list_copy = list_dirs.copy()

    # Checks if the folder is empty
    if len(list_dirs) == 0:
        return

    for file in list_copy:
        full_dir_path = os.path.join(full_path, file)
        if os.path.isfile(full_dir_path):
            os.remove(full_dir_path)
            list_dirs.remove(file)

    for folder in list_dirs:
        delete(os.path.join(path, folder))
        os.rmdir(os.path.join(full_path, folder))


def move_file(full_src_path, full_dst_path):
    src_file = open(full_src_path, 'rb')
    # Concatenating the cwd with the src_path and get the file size.
    size = os.path.getsize(full_src_path)
    # Read file
    bytes = src_file.read(size)
    src_file.close()
    # Creating the file in dst_path and write the bytes in it.
    dst_file = open(full_dst_path, 'wb')
    dst_file.write(bytes)
    dst_file.close()
    os.remove(full_src_path)


def move(src_path, dst_path):
    # Getting the full paths for src and dst paths.
    full_src_path = os.path.join(os.getcwd(), src_path)
    full_dst_path = os.path.join(os.getcwd(), dst_path)
    # Checks if we need to move a folder or a file.
    if os.path.isdir(full_src_path):
        # If it is a folder - create it in dst address.
        os.mkdir(full_dst_path)
        # Getting the list of files/folders in it the current folder.
        list_dirs = os.listdir(full_src_path)
        # Checks if the folder is empty
        if len(list_dirs) == 0:
            return

        # Looping over the items
        for dir in list_dirs:
            # Creating the full path of the item.
            dir_path = os.path.join(full_src_path, dir)
            # If it is a file - call move_file - will delete the file in the end of the func.
            if os.path.isfile(dir_path):
                move_file(full_src_path, full_dst_path)
            # If it's a folder - recursively get call move with the realtive paths.
            elif os.path.isdir(dir_path):
                relative_src = os.path.join(src_path, dir)
                relative_dst = os.path.join(dst_path, dir)
                move(relative_src, relative_dst)
                # Eventually - delete the folder, it must be empty after the recursion.
                os.rmdir(os.path.join (full_src_path, dir))

    # If the path is a file from the beginning- we will just call move_file
    # will copy the file from src to dst, and will delete from the src.
    elif os.path.isfile(full_src_path):
        move_file(full_src_path, full_dst_path)


def execute_commands(s, usr_id, cmp_id):
    # List with size 2, updates[0] = (map)modify updates, updates[1] = (list)the rest.
    updates = users[usr_id][cmp_id]

    # Checks the modify map.
    if len(updates[0].keys()) != 0:
        # Looping over the modify map.
        for update in updates[0].keys():
            # Send the command name to the client
            s.send("Modify".encode())
            wait_for_ack(s)
            # Send the path to the client.
            s.send(update.encode())
            wait_for_ack(s)
            # Send the bytes of the modified path.
            s.sendall(updates[0][update])
            wait_for_ack(s)
            # Deleting the update from the map
            del updates[0][update]

    # Checks the other updates map.
    if len(updates[1]) != 0:
        # Looping over the other updates list.
        for update in updates[1]:
            i = update.find("/")
            command = update[:i]
            _path = update[i + 1:]
            # Send the command name
            s.send(command.encode())
            wait_for_ack(s)
            # Send the path to create.
            # todo Path will hold a '0' or '1' on the first byte to distinguish folder ot file
            s.send(_path.encode())
            wait_for_ack(s)
            if command == "Create":
                # Send the folder/file
                # if os.path.isdir(_path):
                #   send_folder(_path, s)
                if os.path.isfile(_path):
                    # todo The client will get the bytes of the file to create.
                    send_file(_path, s)

            elif command == "Move":
                # path_slash is the index of the slash between src_path and dst_path
                path_slash = _path.find("/")
                dst_path = _path[path_slash + 1:]
                s.send(dst_path.encode())
                # todo  - The client does the move itself from the src to dst.

            # Remove the update (has been done)
            updates[1].remove(update)


# 1. Recieve new data - V
# 2. Execute commands waiting in the buffer - execute_commands V
# 3. Execute the change from the client - create/modify/delete/move
# 4. Pushing this change to all computers buffers #####
#### The paths have to be realtive.
def before_create(s, usr_id, cmp_id):
    # todo - The path from the client will hold '1' or '0' in the first byte - for the directory type
    path = s.recv(1024)
    s.send("ack".encode())
    # Execute commands waiting in the buffer
    execute_commands(s, usr_id, cmp_id)

    # Execute the change from the client:
    create(s, path)


def before_delete(s, usr_id, cmp_id):
    # todo - The path from the client will hold '1' or '0' in the first byte - for the directory type
    path = s.recv(1024)
    s.send("ack".encode())
    # Execute commands waiting in the buffer
    execute_commands(s, usr_id, cmp_id)

    delete(path)

    # Deleting the folder since it's empty.
    os.rmdir(os.path.join(os.getcwd(), path))


def before_move(s, usr_id, cmp_id):
    src_path = s.recv(1024)
    s.send("ack".encode())
    dst_path = s.recv(1024)
    s.send("ack".encode())

    # Execute commands waiting in the buffer
    execute_commands(s, usr_id, cmp_id)

    move(src_path, dst_path)


def before_modify(s, usr_id, cmp_id):
    # todo - The path from the client will hold '1' or '0' in the first byte - for the directory type
    # We will get the path first
    path = s.recv(1024)
    s.send("ack".encode())
    # Execute commands waiting in the buffer
    execute_commands(s, usr_id, cmp_id)
    # Eventually will send the modified file.
    send_file(path,s)

def before_rename(s, usr_id, cmp_id):
    # Getting the src path to change
    src_path = s.recv(1024)
    s.send("ack".encode())
    # Getting the new name:
    name = s.recv(1024)
    s.send("ack".encode())
    # Execute commands waiting in the buffer
    execute_commands(s, usr_id, cmp_id)

    # Renaming the file/folder.
    os.rename(src_path, name)


def check_for_updates(update, s):
    commands = ["Create", "Move", "Modify", "Delete", "Remove"]
    # todo - When implementing the client - start running chronological from here.
    if update in commands:
        s.send("ack".encode())
        data = s.recv(1024)
        s.send("ack".encode())
        i = str(data).rfind("/")
        user_id = str(data)[:i]
        computer_id = str(data)[i + 1:]

        if update == "Create":
            before_create(s, user_id, computer_id)
        if update == "Move":
            before_move(s, user_id, computer_id)
        if update == "Modify":
            pass
        if update == "Delete":
            before_delete(s, user_id, computer_id)
        if update == "Rename":
            before_rename(s, user_id, computer_id)


port = sys.argv[1]
# Dictionary - its key is the id and the value is another dict of computers & list of commands.
users = {}

path = ""
user_id = ""
data = ""
origin_cwd = os.getcwd()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12347))
server.listen(5)
while True:
    path = ""
    user_id = ""

    client_socket, client_address = server.accept()
    data = client_socket.recv(1024).decode()

    # For monitored Clients
    check_for_updates(data, client_socket)

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
        users[user_id][computer_id] = [{}, []]
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
        computer_id = str(len(users[data].keys()) + 1)
        # Creating new dict for the  commands - commands[0]=modify commands, commands[1]= the rest commands.
        users[data][computer_id] = [{}, []]
        client_socket.send(computer_id.encode())  # Sending an acknowledgment.
        # Waiting for ack
        wait_for_ack(client_socket)
        send_folder(os.path.join(os.getcwd(), user_id), client_socket)

    client_socket.close()
    os.chdir(origin_cwd)
    print('Client disconnected')
