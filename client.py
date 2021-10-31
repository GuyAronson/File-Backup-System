from socket import socket, AF_INET, SOCK_DGRAM
import sys


# def removing_breaklines(str):
# 	lst = str.split('\\n')
# 	string = ""
# 	for s in lst:
# 		string = string + s + "\n"

# 	return string


def main():
    # arguments from command line
    ip = sys.argv[1]
    port = sys.argv[2]
    file_name = sys.argv[3]

    # defining a socket
    s = socket(AF_INET, SOCK_DGRAM)
    s.settimeout(10)


    # Reading from a file as bytes
    file = open(file_name, "rb")
    message = file.read()
    chars_amount = len(message)

    if chars_amount > 50000:
        raise Exception("Too many bytes. More than 50k")

    drops = 0  # delete
    #make sure the last package will be sent
    if float(int(chars_amount / 96)) < chars_amount / 96:
        packages_amount = int(chars_amount / 96) + 1
    else:
        packages_amount = int(chars_amount / 96)
    package_number = 0
    i = 0
    is_first_message = True
    single_message = ""
    data = ""

    # the variable i runs on bytes in the text, increments by 100 each loop
    while i < chars_amount:
        if is_first_message:
            # Sending the first message - contains the amount of packages will be sent.
            single_message = int.to_bytes(packages_amount, 2, 'big')
            s.sendto(single_message, (ip, int(port)))
        else:
            # Taking the first 100 bytes from the file
            if package_number <= 9:
                single_message = bytes(0) + bytes(0) + int.to_bytes(package_number, 2, 'big')
            elif package_number <= 99:
                single_message = bytes(0) + int.to_bytes(package_number, 2, 'big')
            else:
                single_message = int.to_bytes(package_number, 2, 'big')
            single_message += message[i:i + 98]
            i += 98
            s.sendto(single_message, (ip, int(port)))

        try:
            data, addr = s.recvfrom(1024)
        except OSError:
            if not is_first_message:
                i = i - 98

        if data == single_message:
            if is_first_message:
                is_first_message = False
                print("I got the same message i sent! (first message)")  # delete
            else:
                package_number += 1
                print(f"I got the same message i sent! package: {package_number}")  # delete
        else:  # delete
            if not is_first_message:
                i = i - 98
            drops += 1  # delete
            print(f'oh no, bad message, drop number {drops}')  # delete

        print(str(i))

    print("file has been transferred")
    s.close()

    return 0


if __name__ == "__main__":
    main()