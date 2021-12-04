import socket
import string
import os

# 2^10 is the small buffer bytes.
BUFFER = 1024
DONE = "Done Folder"


def wait_for_ack(s):
    data = "0"
    while data != "ack":
        data = s.recv(3).decode()


# Function to recieve a single file.
def recv_file(file_dir, client_socket):
    data = b''
    # initializing a byte array for the file's bytes
    bytes = bytearray()
    # Getting the file size
    file_size = int.from_bytes(client_socket.recv(10), 'big')
    client_socket.send("ack".encode())
    # Open the file.
    file = open(file_dir, 'wb')

    # Looping while the file_size is bigger than the length of the bytes we recieved.
    while file_size > len(bytes):
        # trying to receive the rest of the bytes left.
        data = client_socket.recv(file_size - len(bytes))
        # If we didn't receive any data, we can exit the loop
        if len(data) == 0:
            break
        # Add the data to the bytes array.
        bytes.extend(data)
    # Eventually writing all the bytes into the file.
    file.write(bytes)

    # Double ack to make sure everything worked.
    client_socket.send("ack".encode())
    wait_for_ack(client_socket)
    file.close()


def send_file(directory, s):
    # Get the file size in bytes
    file_size = os.path.getsize(directory)
    # Send the size of the file to the server
    bytes = file_size.to_bytes(10, 'big')
    s.send(bytes)
    wait_for_ack(s)
    # Open & read the file
    file = open(directory, 'rb')

    # Looping while there are bytes left to read.
    while file_size > 0:
        # Trying to read what left from the file.
        data = file.read(file_size)
        # Sending the segment we read.
        s.send(data)
        # the data left to read is smaller.
        file_size = file_size - len(data)

    # Double ack.
    wait_for_ack(s)
    s.send("ack".encode())
    file.close()


# Function to recieve a folder and its sub-directories.
############### Change the recieve bytes ###################
def recv_folder(client_socket):
    # Saving the original working directory.
    cwd = os.getcwd()
    # First, recieve relative root directory .
    data = client_socket.recv(BUFFER).decode()
    client_socket.send("ack".encode())
    dir_name = os.path.join(cwd, data[1:])
    while data != DONE:
        # Got the full root's path
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        # Change working directory to the full root's path
        os.chdir(dir_name)

        # Getting the first file/folder relative directory.
        data = client_socket.recv(BUFFER).decode()
        client_socket.send(("ack").encode())
        data = data.rstrip()
        data = data.lstrip()
        # Checks if the client stopped sending info.
        if data == DONE:
            break

        # Extracting the key & the directory name
        is_dir = int(data[0])
        dir_name = os.path.join(cwd, data[1:])

        # Running while there are files in the directory.
        while is_dir == 1:
            # Getting the file.
            recv_file(dir_name, client_socket)
            # Getting the next file/folder realtive directory
            data = (client_socket.recv(BUFFER)).decode()
            if data != DONE:
                client_socket.send(("ack").encode())
                is_dir = int(data[0])
                dir_name = os.path.join(cwd, data[1:])
            else:
                is_dir = 0


def send_folder(directory, s):
    # Changing directory to the realtive directory.
    os.chdir(os.path.join(os.getcwd(), directory))
    cwd = os.getcwd()
    # Saving the start index of the relative directory
    start_relative_index = cwd.rfind("/")
    for (root, dirs, files) in os.walk(os.getcwd(), topdown=True):
        # Sending the root directory.
        a = ("0" + root[start_relative_index + 1:])
        s.send(a.encode())
        wait_for_ack(s)

        # Sending the files.
        for file in files:
            relative_file_dir = os.path.join(root[start_relative_index + 1:], file)
            file_dir = os.path.join(root, file)
            # Sending the relative file directory to the server.
            s.send(("1" + relative_file_dir).encode())
            wait_for_ack(s)
            send_file(file_dir, s)
    s.send(DONE.encode())


