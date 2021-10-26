from socket import socket, AF_INET, SOCK_DGRAM
import sys

# def removing_breaklines(str):
# 	lst = str.split('\\n')
# 	string = ""
# 	for s in lst:
# 		string = string + s + "\n"

# 	return string


def main():
	#arguments from command line
	ip = sys.argv[1]
	port = sys.argv[2]
	file_name = sys.argv[3]

	#defining a socket
	s = socket(AF_INET, SOCK_DGRAM)

	#Reading from a file
	file = open(file_name, "r")
	message = file.read()
	chars_amount = len(message)
	
	i = 0
	while i <= chars_amount:
		#Taking the first 100 bytesq/chars from the file
		small_message = message[i:i+100]
		#print(small_message)
		s.sendto(bytes(small_message, 'utf-8'), (ip, int(port)))
		i += 100

		data, addr = s.recvfrom(1024)
		#new_data = str(data)

		#data = removing_breaklines(new_data[2:len(new_data)-1])
		#print(data)

		if data == bytes(small_message, 'utf-8'):
			print("I got the same message i sent!")
		else:
			print("oh no, bad message")
			break
	
	print("file has been trasnferred")
	s.close()

	return 0;


if __name__ == "__main__":
	main()