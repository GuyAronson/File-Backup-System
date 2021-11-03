import socket
import sys


def main():
    if len(sys.argv) != 2:
        sys.exit(1)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except Exception:
        sys.exit(1)

    s.bind(('', int(sys.argv[1])))
    last_message = ""
    while True:
        packages = []
        packages_amount = 0

        # Making sure that the first message with the amount of packages will arrive.
        is_first_message = True
        while is_first_message:
            data, addr = s.recvfrom(1024)

            # if we get the last message, but it dropped. send it again.
            if data == last_message:
                s.sendto(data, addr)
            else:
                packages_amount = int.from_bytes(data, "big")
                is_first_message = False
                s.sendto(data, addr)  # Sending an acknowledgment message.

        packages_received = 0

        while packages_received < packages_amount:
            data, addr = s.recvfrom(1024)

            # Checks if the current message is the first message received.
            if data == int.to_bytes(packages_amount, 2, "big"):
                s.sendto(data, addr)
                continue

            package_num = int.from_bytes(data[0:2], 'big')  # Getting the package number - 3 first bytes.
            message = data[2:]  # Saving the message without the package number

            if package_num == packages_received:
                packages.append(message)  # adding the message to the list
                packages_received += 1  # increment the counter
                s.sendto(data, addr)  # sending back the same message.
                if package_num == packages_amount - 1:  # if last message, save it
                    last_message = data
            elif package_num == packages_received - 1:
                # Which means we got the same message as before,
                # we will just sent an acknowledgement message
                s.sendto(data, addr)

        for st in packages:
            print(str(st, 'utf-8'), end="")


if __name__ == "__main__":
    main()