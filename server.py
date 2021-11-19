import socket
import sys
import string
import random
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import os

# os.chdir(path)

port = sys.argv[0]

id_list = []

path = ""
id = ""
is_dir = 0

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
    os.chdir(os.getcwd() + "/" + id)    # Changing the current working directory

    is_dir = data[0]	# If the key is 0 - then it's a directory, if it's 1 then it's a file.
    path += data[1:]    # The relative directory with out the key.

    last_slash_index = path.rfind("/")
    if last_slash_index != -1:

    	#create a relative directory 1 step before the final one.
    	os.makedirs(path[:last_slash_index])
    	# Changing the current working directory
		os.chdir(os.getcwd() + "/" + path[:last_slash_index])  

    if is_dir == 0:
    	# todo - create a directory
    	# todo - back up the entire directory.
    else:
    	# todo - create & backup file.
    	

    
    client_socket.close()
    print('Client disconnected')
