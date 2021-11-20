import socket
import sys
import string
import random
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os

port = sys.argv[0]

id_list = []

path = ""
id = ""
is_dir = 0
origin_cwd = os.getcwd()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12345))
server.listen(5)
while True:
    client_socket, client_address = server.accept()
    data = client_socket.recv(1024)

    # if id is not in id_list - create random one and send it.
    if data not in id_list:
        # Create a random id.
        id = ''.join((random.choices(string.ascii_lowercase + string.digits, k=128)))
        id_list.append(id)
        os.mkdir(id)
        client_socket.send(bytes(id, 'utf-8')) # Sending an acknowledgment - ***may move to another location***
    # Id is in the list - the client is already registered.
    else:
        id = data
        client_socket.send(bytes(id, 'utf-8'))  # Sending an acknowledgment.
        data = client_socket.recv(1024)         # The data now should be the directory to backup

    os.chdir(origin_cwd + "/" + id)    # Changing the current working directory

    is_dir = data[0]	# If the key is 0 - then it's a directory, if it's 1 then it's a file.
    path += data[1:]    # The relative directory with out the key.

    last_slash_index = path.rfind("/")

    # Checks if there is a / in the path - which means there are subdirectories.
    if last_slash_index != -1:

    	#create a relative directory 1 step before the final one.
    	os.makedirs(path[:last_slash_index])
    	# Changing the current working directory
		os.chdir(origin_cwd + "/" + path[:last_slash_index])  

	dir_name = path[last_slash_index + 1:] 
    if is_dir == 0:
    	# todo - back up the entire folder.
    	recv_folder(dir_name, client_socket, client_address)
    else:
    	# todo - create & backup file.
    	# Removing the exisiting file
    	if os.path.exists(dir_name):
    		os.remove(dir_name)
    	recv_file(dir_name, client_socket, client_address)

    
    client_socket.close()
    print('Client disconnected')

#Function to recieve a single file.
def recv_file(file_name, client_socket, client_address):
	# Open the file.
	file = open(file_name, 'wb')
	# Getting the first chunk of bytes.
	chunk = client_socket.recv(1024)
	while chunk:
		# Writing the bytes while the chunk isn't empty.
		file.write(chunk)
		chunk = client_socket.recv(1024)
	file.close()

# Function to recieve a folder and its sub-directories.
def recv_folder(dir_name, client_socket, client_address):
	is_dir = 0
	dir_name = ""
	# Saving the original working directory.
	cwd = os.getcwd()
	# First root recieve.
	data = client_socket.recv(1024)
	# Extracting the key & the root name
	is_dir = data[0]
	dir_name = data[1:]
	while data:
		# Got the root path of the directory
		os.makedirs(dir_name)
		# Change working directory.
		os.chdir(cwd + "/" + data)

		# Getting the first file/folder name.
		data = client_socket.recv(1024)
		
		# Checks if the client stopped sending info.
		if !data:
			break

		# Extracting the key & the directory name	
		is_dir = data[0]
		dir_name = data[1:]

		#Running while there are files in the directory.
		while is_dir == 1:
			# Getting the file.
			recv_file(dir_name, client_socket, client_address)
			# Getting the next file/folder name
			data = client_socket.recv(1024)
			is_dir = data[0]
			dir_name = data[1:]

		#is_dir = 0,  This is a folder
		data = dir_name