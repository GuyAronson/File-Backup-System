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
        recv_folder(s)

def modify(path, bytes):
    pass

def delete(s, path):
    pass

def move(s, src_path, dst_path):
    pass

def execute_commands(s, usr_id, cmp_id):
    # List with size 2, updates[0] = modify updates, updates[1] = the rest.
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
            s.send(updates[0][update])

            # Deleting the update from the map
            del updates[0][update]
    # Checks the other updates map.
    if len(updates[1]) != 0:
        # Looping over the other updates list.
        for update in updates[1]:
            i = update.find("/")
            command = update[:i]
            _path = update[i+1:]
            # Send the command name
            s.send(command.encode())
            wait_for_ack(s)
            # Send the path to create.
            s.send(_path.encode())
            wait_for_ack(s)
            if command == "Create":
                # Send the folder/file
                if os.path.isdir(_path):
                    send_folder(_path, s)
                elif os.path.isfile(_path):
                    send_file(_path, s)
            elif command == "Move":
                # path_slash is the index of the slash between src_path and dst_path
                path_slash = _path.find("/")
                dst_path = _path[path_slash + 1:]
                s.end(dst_path.encode())
                # The client does the move itself.


            # Remove the update (has been done)
            updates[1].remove(update)



def before_create(s, usr_id, cmp_id):
    path  = s.recv(1024)
    s.send("ack".encode())
    execute_commands(s, usr_id, cmp_id)






def before_delete(s, usr_id, cmp_id):
    updates = users[usr_id][cmp_id]

def before_move(s):
    pass

def before_modify(s):
    pass

def check_for_updates(update, s):
    s.send("ack".encode())
    data = s.recv(1024)
    s.send("ack".encode())
    i = data.rfind("/")
    user_id = data[:i]
    computer_id = data[i + 1:]
    s.send("ack".encode())

    if update == "Create":
        before_create(s, user_id, computer_id)
    if update == "Move":
        pass
    if update == "Modify":
        pass
    if update == "Delete":
        before_delete(s, user_id, computer_id)


port = sys.argv[1]
# Dictionary - its key is the id and the value is another dict of computers & list of commands.
users = {}

path = ""
user_id = ""
data = ""
origin_cwd = os.getcwd()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12345))
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
        users[data] = {}
        # This is the first computer - the id is 1
        computer_id = '1'
        # Creating new dict for the  commands - commands[0]=modify commands, commands[1]= the rest commands.
        users[data][computer_id] = [{}, []]
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
