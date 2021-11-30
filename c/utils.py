import socket
import string
import os

# Function to recieve a single file.
def recv_file(file_dir, client_socket):
    file_size = int.from_bytes(client_socket.recv(8), 'big')
    # Open the file.
    file = open(file_dir, 'wb')
    # Getting the first chunk of bytes.
    data = client_socket.recv(file_size)
    file.write(data)
    file.close()


# Function to recieve a folder and its sub-directories.
############### Change the recieve bytes ###################
def recv_folder(client_socket):
    # Saving the original working directory.
    cwd = os.getcwd()
    # First, recieve relative root directory .
    data = client_socket.recv(1024).decode()
    client_socket.send("ack".encode())
    dir_name = os.path.join(cwd, data[1:])
    while data != "":
        # Got the full root's path
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        # Change working directory to the full root's path
        os.chdir(dir_name)

        # Getting the first file/folder relative directory.
        data = client_socket.recv(1024).decode()
        client_socket.send(("ack").encode())
        data = data.rstrip()
        data = data.lstrip()
        # Checks if the client stopped sending info.
        if data == "":
            break

        # Extracting the key & the directory name
        is_dir = int(data[0])
        dir_name = os.path.join(cwd, data[1:])

        # Running while there are files in the directory.
        while is_dir == 1:
            # Getting the file.
            recv_file(dir_name, client_socket)
            # Getting the next file/folder realtive directory
            data = client_socket.recv(1024).decode()
            if data != "":
                client_socket.send(("ack").encode())
                is_dir = int(data[0])
                dir_name = os.path.join(cwd, data[1:])
            else:
                is_dir = 0


def wait_for_ack(s):
    data = "0"
    while data != "ack":
        data = s.recv(3).decode()


def send_file(directory, s):
    # Get the file size in bytes
    file_size = os.path.getsize(directory)
    # Send the size of the file to the server
    bytes = file_size.to_bytes(8, 'big')
    s.send(bytes)
    # Open & read the file
    file = open(directory, 'rb')
    data = file.read(file_size)
    # Send all.
    s.sendall(data)
    file.close()


def send_folder(directory, s):
    # Changing directory to the realtive directory.
    os.chdir(os.path.join(os.getcwd(), directory))
    cwd = os.getcwd()
    # Saving the start index of the relative directory
    start_relative_index = cwd.rfind("/")
    for (root, dirs, files) in os.walk(os.getcwd(), topdown=True):
        # Sending the root directory.
        a = ("0"+root[start_relative_index+1:])
        s.send(a.encode())
        wait_for_ack(s)

        # Sending the files.
        for file in files:
            relative_file_dir = os.path.join(root[start_relative_index+1:], file)
            file_dir = os.path.join(root, file)
            # Sending the relative file directory to the server.
            s.send(("1" + relative_file_dir).encode())
            wait_for_ack(s)
            send_file(file_dir, s)

# todo When a change in the client folder has been made - we need to notify to the server.
# The server need to distinguish which change is it - Send a package with the change's name
# modify/create/delete/move
# todo - the server needs to complete the same change.
# todo - then the server needs to do the changes in the other computers in the same id.
# the server does the change only when a computer logs in,
# and save the change for the other computers when they log in.
# The server will hold the changes to do per computer in a specific buffer per computer.



