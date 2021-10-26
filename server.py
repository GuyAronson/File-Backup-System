import socket
import sys

def main():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind(('', int(sys.argv[1])))

	while True:
		data, addr = s.recvfrom(1024)
		print(str(data), addr)
		s.sendto(data, addr)

if __name__ == "__main__":
	main()