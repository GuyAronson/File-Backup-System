import socket
import sys


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', int(sys.argv[1])))

    packages = []
    packages_amount = 0

    # Making sure that the first message with the amount of packages will arrive.
    is_first_message = True
    while is_first_message:
        data, addr = s.recvfrom(1024)
        packages_amount = int.from_bytes(data, "big")
        is_first_message = False
        s.sendto(data, addr)  # Sending an acknowledgment message.

    print("packages_amount: " + str(packages_amount))
    packages_received = 0

    while packages_received < packages_amount:
        data, addr = s.recvfrom(1024)
        print("data: " + str(data))

        package_num = int.from_bytes(data[0:2], 'big')  # Getting the package number - 3 first bytes.
        message = data[2:]  # Saving the message without the package number
        print("package num: " + str(package_num))
        print("package rec: " + str(packages_received))
        if package_num == packages_received:
            packages.append(message)  # adding the message to the list
            packages_received += 1  # increment the counter
            s.sendto(data, addr)  # sending back the same message.
        elif package_num == packages_received - 1:
            # Which means we got the same message as before,
            # we will just sent an acknowledgement message
            s.sendto(data, addr)

    # What if the server drops the last package - the client will not know that the server got it,
    # The server finished his program, while client is still sending.

    for st in packages:
        print(str(st, 'utf-8'), end="")
    print()


if __name__ == "__main__":
    main()
