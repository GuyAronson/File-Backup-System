
# todo- The client will send a 1 or 0 as a key - to know whether is it a file or a directory to back up on the server.
# after registaration in the server - the client will monitor the files - using watchdog
# When a change has been made - the client will send a request for backup to the server.



# def recv_folder(dir_name, client_socket, client_address):

#     for (root,dirs,files) in os.walk(dir_name, topdown=true):
#     	# Create the dir using root
# 		os.mkdir(root)
# 		# Changing directory
# 		os.chdir(os.getcwd() + "/" + root)
#         # Back up the files using recv_file
#         print (files)