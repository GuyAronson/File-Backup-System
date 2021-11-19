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

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12345))
server.listen(5)
while True:
    client_socket, client_address = server.accept()
    data = client_socket.recv(100)

    # if id is not in id_list - create random one and send it.
    if data not in id_list:
        id = ''.join((random.choices(string.ascii_lowercase + string.digits, k=128)))
        client_socket.send(bytes(id, 'utf-8'))
    last_slash_index = data.rfind("/")
    if last_slash_index == -1:
        #todo create file name data
    else:
        data[last_slash_index:].rfind(".")
     os.makedirs(data)



    client_socket.close()
    print('Client disconnected')