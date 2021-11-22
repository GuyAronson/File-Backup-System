from socket import socket, AF_INET, SOCK_DGRAM
import sys

def main():
    # arguments from command line
    if len(sys.argv) != 4:
        sys.exit(1)
    else:
        port = sys.argv[1]
        ip = sys.argv[2]
        file_name = sys.argv[3]


    # defining a socket
    try:
        s = socket(AF_INET, SOCK_DGRAM)
    except Exception:
        sys.exit(1)
    s.settimeout(10)

    # Reading from a file as bytes
    try:
        file = open(file_name, "rb")
    except OSError:
        s.close()
        sys.exit(1)
    message = file.read()
    chars_amount = len(message)

    if chars_amount > 50000:
        s.close()
        sys.exit(1)

    packages_amount = 0

    #make sure the last package will be sent
    if float(int(chars_amount / 96)) < (chars_amount / 96):
        packages_amount += int(chars_amount / 96) + 1
    else:
        packages_amount += int(chars_amount / 96)
    package_number = 0
    i = 0
    is_first_message = True
    data = ""

    # the variable i runs on bytes in the text, increments by 100 each loop
    while i < chars_amount:
        if is_first_message:
            # Sending the first message - contains the amount of packages will be sent.
            single_message = int.to_bytes(packages_amount, 2, 'big')
            s.sendto(single_message, (ip, int(port)))
        else:
            single_message = int.to_bytes(package_number, 2, 'big')
            single_message += message[i:i + 98]
            i += 98
            s.sendto(single_message, (ip, int(port)))

        try:
            data, addr = s.recvfrom(1024)
        except OSError:
            pass

        if data == single_message:
            if is_first_message:
                is_first_message = False
            else:
                package_number += 1
        else:
            if not is_first_message and i > 0:
                i = i - 98
    s.close()

    return 0

if __name__ == "__main__":
    main()
