import socket
import string
import os

# 2^12 is the buffer bytes.
BIG_BUFFER = 8192
# 2^10 is the small buffer bytes.
SMALL_BUFFER = 1024
DONE = "Done Folder"


def wait_for_ack(s):
    data = "0"
    while data != "ack":
        data = s.recv(3).decode()


# Function to recieve a single file.
def recv_file(file_dir, client_socket):
    data = b'0'
    file_size = int.from_bytes(client_socket.recv(10), 'big')
    print("recieve file_size" + str(file_size))
    client_socket.send("ack".encode())
    # Open the file.
    file = open(file_dir, 'wb')
    #with open(file_dir, mode='wb', errors='ignore') as file:
    count = file_size / BIG_BUFFER
    while file_size >= BIG_BUFFER:
        print("Segment " + str(count) + "  file_size: " + str(file_size))
        count -= 1
        # Getting the whole file.
        data = client_socket.recv(BIG_BUFFER)
        file.write(data)
        file_size = file_size - BIG_BUFFER
    print("Should finish...")

    if file_size > 0:
        print("Segment " + str(count) + "  file_size: " + str(file_size))
        data = client_socket.recv(BIG_BUFFER)
        file.write(data)
    print("Done")
    print("Data: " + data.decode())
    file.close()
    client_socket.send("ack".encode())
    wait_for_ack(client_socket)
    print("Acked. ")


def send_file(directory, s):
    # Get the file size in bytes
    file_size = os.path.getsize(directory)
    print("sent file_size " + str(file_size))
    # Send the size of the file to the server
    bytes = file_size.to_bytes(10, 'big')
    s.send(bytes)
    wait_for_ack(s)
    # Open & read the file
    file = open(directory, 'rb')
    count = file_size / BIG_BUFFER
    while file_size >= BIG_BUFFER:
        print("Segment " + str(count) + "  file_size: " + str(file_size))
        count -= 1
        data = file.read(BIG_BUFFER)
        s.send(data)
        file_size = file_size - BIG_BUFFER

    if file_size > 0:
        print("Segment " + str(count) + "  file_size: " + str(file_size))
        data = file.read(BIG_BUFFER)
        s.send(data)

    file.close()
    wait_for_ack(s)
    s.send("ack".encode())
    print("Acked. ")


# Function to recieve a folder and its sub-directories.
############### Change the recieve bytes ###################
def recv_folder(client_socket):
    # Saving the original working directory.
    cwd = os.getcwd()
    # First, recieve relative root directory .
    data = client_socket.recv(SMALL_BUFFER).decode()
    print("directory: " + data)
    client_socket.send("ack".encode())
    dir_name = os.path.join(cwd, data[1:])
    while data != DONE:
        # Got the full root's path
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        # Change working directory to the full root's path
        os.chdir(dir_name)

        # Getting the first file/folder relative directory.
        data = client_socket.recv(SMALL_BUFFER).decode()
        print("directory: " + data)
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
            data = (client_socket.recv(SMALL_BUFFER)).decode()
            print("directory: " + data)
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
        print("directory: " + a)
        s.send(a.encode())
        wait_for_ack(s)

        # Sending the files.
        for file in files:
            relative_file_dir = os.path.join(root[start_relative_index + 1:], file)
            file_dir = os.path.join(root, file)
            # Sending the relative file directory to the server.
            s.send(("1" + relative_file_dir).encode())
            print("directory: " + relative_file_dir)
            wait_for_ack(s)
            send_file(file_dir, s)
    s.send(DONE.encode())

# todo When a change in the client folder has been made - we need to notify to the server.
# The server need to distinguish which change is it - Send a package with the change's name
# modify/create/delete/move
# todo - the server needs to complete the same change.
# todo - then the server needs to do the changes in the other computers in the same id.
# the server does the change only when a computer logs in,
# and save the change for the other computers when they log in.
# The server will hold the changes to do per computer in a specific buffer per computer.
