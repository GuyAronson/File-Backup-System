import socket
import string
import os

# 2^10 is the small buffer bytes.


BUFFER = 1024
DONE = "Done Folder"
ACK = "ack".encode()


# Function that makes the program wait for ack in a loop.
def wait_for_ack(s):
    data = "0"
    while data != "ack":
        if data == "ign":
            return "ignore"
        data = s.recv(3).decode()


# Function to recieve a single file - file_dir is a full directory
def recv_file(file_dir, client_socket):
    data = b''
    # initializing a byte array for the file's bytes
    bytes = bytearray()
    # Getting the file size
    file_size = int.from_bytes(client_socket.recv(10), 'big')
    client_socket.send(ACK)
    # Open the file - file_dir is the full directory.
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
    client_socket.send(ACK)
    wait_for_ack(client_socket)
    file.close()


# Function to receive a single file - directory is a full directory
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
    s.send(ACK)
    file.close()


# Function to recieve a folder and its sub-directories.
def recv_folder(client_socket):
    # Saving the original working directory.
    cwd = os.getcwd()
    # First, recieve relative root directory .
    data = client_socket.recv(BUFFER).decode()
    client_socket.send(ACK)
    dir_name = os.path.join(cwd, data[1:])
    while data != DONE:
        # Got the full root's path
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        # Change working directory to the full root's path
        os.chdir(dir_name)

        # Getting the first file/folder relative directory.
        data = client_socket.recv(BUFFER).decode()
        client_socket.send(ACK)
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
                client_socket.send(ACK)
                is_dir = int(data[0])
                dir_name = os.path.join(cwd, data[1:])
            else:
                is_dir = 0


# Function to send a folder and its sub-folders.
# directory is a full dir.
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


# function to create a folder/file - path is a full directory
def create(s, path):
    # if is_dir = 0 , it;s a directory, if is_dir =1 it's a file.
    is_dir = path[0]
    # The relative directory.
    directory = path[1:]
    full_dir = os.path.join(os.getcwd(), directory)
    if is_dir == '1':
        recv_file(full_dir, s)
    elif is_dir == '0':
        os.mkdir(full_dir)


# Execute the modify command - needs to receive the bytes to modify.
# Path is a full directory
def modify(s, path):
    # Get the full path - must be a file.
    full_path = os.path.join(os.getcwd(), path[1:])
    recv_file(full_path, s)


# Function to recursively delete a folder  - path is a full directory
def delete(path):
    # path is a relative path.
    full_path = os.path.join(os.getcwd(), path)

    # Checks if the path is a file
    if os.path.isfile(full_path):
        os.remove(full_path)
        return

    # Creating list of all items within the given folder.
    list_dirs = os.listdir(full_path)
    list_copy = list_dirs.copy()

    # Checks if the folder is empty
    if len(list_dirs) == 0:
        return

    # Looping over the files - delete them all in the given folder.
    for file in list_copy:
        full_dir_path = os.path.join(full_path, file)
        if os.path.isfile(full_dir_path):
            os.remove(full_dir_path)
            list_dirs.remove(file)

    # loop over the sub-folders and recursively delete them.
    for folder in list_dirs:
        full_folder_path = os.path.join(full_path, folder)
        delete(full_folder_path)
        os.rmdir(full_folder_path)


# function to move a specific file from src to dst path.
def move_file(full_src_path, full_dst_path):
    src_file = open(full_src_path, 'rb')
    # Get the size of the file.
    size = os.path.getsize(full_src_path)
    bytes_to_write = bytearray()

    # Read the file as much as possible,
    # add it to the bytes array, and decrease the file's size till 0.
    while size > len(bytes_to_write):
        # Each loop reading the exact amount of bytes left to read.
        data = src_file.read(size - len(bytes_to_write))
        bytes_to_write.extend(data)

    src_file.close()
    # Creating the file in dst_path and write all bytes in it.
    dst_file = open(full_dst_path, 'wb')
    dst_file.write(bytes_to_write)
    dst_file.close()

    # Removing the source file.
    os.remove(full_src_path)


# function to recursively move an entire folder.
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
            src_dir_path = os.path.join(full_src_path, dir)
            dst_dir_path = os.path.join(full_dst_path, dir)
            # If it is a file - call move_file - will delete the file in the end of the func.
            if os.path.isfile(src_dir_path):
                move_file(src_dir_path, dst_dir_path)
            # If it's a folder - recursively get call move with the realtive paths.
            elif os.path.isdir(src_dir_path):
                # Create realtive paths
                relative_src = os.path.join(src_path, dir)
                relative_dst = os.path.join(dst_path, dir)
                move(relative_src, relative_dst)
                # Eventually - delete the folder, it must be empty after the recursion.
                os.rmdir(src_dir_path)

    # If the path is a file -  we will just call move_file
    # it will copy the file from src to dst, and will delete from the src.
    elif os.path.isfile(full_src_path):
        move_file(full_src_path, full_dst_path)


# Adding all updates to the list - with 1 path.
def add_all_updates(updates, command, path):
    # path is a relative path.
    full_path = os.path.join(os.getcwd(), path)

    # Checks if the path is a file
    if os.path.isfile(full_path):
        # Updating the ignored updates list in the client
        updates.append(command + "$" + path)
        return

    # Creating list of all items within the given folder.
    list_dirs = os.listdir(full_path)

    # Checks if the folder is empty
    if len(list_dirs) == 0:
        # Updating the ignored updates list in the client
        updates.append(command + "$" + path)
        return

    # Running on all files/folders in the folder.
    for dir in list_dirs:

        # Add the update to the updates list.
        updates.append(command + "$" + os.path.join(path, dir))

        # Creating full directory for the dir.
        full_dir_path = os.path.join(full_path, dir)

        # If it's a folder, we run recrursively on its sub-directories.
        if os.path.isdir(full_dir_path):
            add_all_updates(updates, command, os.path.join(path, dir))


# Overloading -
# Adding all updates to the list - with 2 paths.
def add_all_updates(updates, command, src_path, dst_path):
    # the paths are a relative path.
    full_src_path = os.path.join(os.getcwd(), src_path)
    full_dst_path = os.path.join(os.getcwd(), dst_path)

    # Checks if the src_path is a file
    if os.path.isfile(full_src_path):
        # Updating the ignored updates list in the client
        updates.append(command + "$" + src_path + "$" + dst_path)
        return

    # Creating list of all items within the given folder.
    list_dirs = os.listdir(full_src_path)

    # Checks if the folder is empty
    if len(list_dirs) == 0:
        # Updating the ignored updates list in the client
        updates.append(command + "$" + src_path + "$" + dst_path)
        return

    # Running on all files/folders in the folder.
    for dir in list_dirs:

        # Add the update to the updates list.
        updates.append(command + "$" + os.path.join(src_path, dir) + "$" + os.path.join(dst_path, dir))

        # Creating full directory for the dir.
        full_src_dir_path = os.path.join(full_src_path, dir)

        # If it's a folder, we run recrursively on its sub-directories.
        if os.path.isdir(full_src_dir_path):
            add_all_updates(updates, command, os.path.join(src_path, dir), os.path.join(dst_path, dir))