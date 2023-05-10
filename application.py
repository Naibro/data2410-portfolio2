'''
    #Utility functions: 1) to create a packet of 1472 bytes with header (12 bytes) (sequence number, acknowledgement number,
    #flags and receiver window) and applicaton data (1460 bytes), and 2) to parse
    # the extracted header from the application data.

    Qs:
    should packet #1 be discarded by the receiver in GBN if #2 wasn't received
    should window size be fixed, as of the Github readme or set by the receiver
'''
from struct import *
import time
import socket
import argparse
import sys
import ipaddress

# ARGUMENT PARSER #
parser = argparse.ArgumentParser(
    prog='DRTP application',
    description='Transfers a file between a client and a server using DRTP')

# Arguments used for the client/sender
parser.add_argument('-c', '--client', action='store_true', help='enable client mode')
parser.add_argument('-f', '--file', type=str, choices=['picture.gif'], help='input a file to be sent')

# Arguments used for the server/receiver
parser.add_argument('-s', '--server', action='store_true', help='enable server mode')

# Arguments common for both server and client
parser.add_argument('-p', '--port', type=int, default=8088, help='allows selection of a port', metavar='[1024-65535]')
parser.add_argument('-i', '--ipaddress', type=str, default='127.0.0.1', help='allows selection of an ip-address')
parser.add_argument('-r', '--reliability', choices=['stop-and-wait', 'GBN', 'SR'], required=True,
                    help='allows selection of different reliability functions')
parser.add_argument('-t', '--test', type=str, choices=['skip_ack', 'skip_seq'],
                    help='selection of which test case to run')

args = parser.parse_args()  # Start the argument parser and its arguments

# MAIN PROGRAM #

# I integer (unsigned long) = 4bytes and H (unsigned short integer 2 bytes)
# see the struct official page for more info

header_format = '!IIHH'


# A function that checks that the IP-address is valid
def check_ip(address):
    # Tries to take an IP-address in
    try:
        # IP-address is valid
        val = ipaddress.ip_address(address)
        # print(f"The IP address {val} is valid.")

    # If it does not work, an error is raised
    except ValueError:
        print(f"The IP address is {address} not valid")
        sys.exit()


# A function that checks that the port is valid
def check_port(val):
    # Tries to take a port in, making it to an integer
    try:
        value = int(val)
    # If not, it raises an error
    except ValueError:
        raise argparse.ArgumentTypeError('expected an integer but you entered a string')
    # Also, if the input is over 65535, the system will print an error msg and exit
    if value > 65535:
        print('port cannot be higher than 65535')
        sys.exit()
    # The same happens if the port is less than 1024
    elif 0 <= value < 1024:
        print('port cannot be less than 1024')
        sys.exit()
    # And even when the input of the port is a negative value
    elif value < 0:
        print('port cannot be a negative value')
        sys.exit()
    return value  # Lastly, the checked port will be returned and used in the program


def create_packet(seq, ack, flags, win, data):
    # creates a packet with header information and application data
    # the input arguments are sequence number, acknowledgment number
    # flags (we only use 4 bits),  receiver window and application data
    # struct.pack returns a bytes object containing the header values
    # packed according to the header_format !IIHH
    header = pack(header_format, seq, ack, flags, win)

    # once we create a header, we add the application data to create a packet
    # of 1472 bytes
    packet = header + data
    # print(f'packet containing header + data of size {len(packet)}')  # just to show the length of the packet
    return packet


def parse_header(header):
    # taks a header of 12 bytes as an argument,
    # unpacks the value based on the specified header_format
    # and return a tuple with the values
    header_from_msg = unpack(header_format, header)
    # parse_flags(flags)
    return header_from_msg


def parse_flags(flags):
    # we only parse the first 3 fields because we're not
    # using rst in our implementation
    syn = flags & (1 << 3)
    ack = flags & (1 << 2)
    fin = flags & (1 << 1)
    return syn, ack, fin


def send_format(file, seq):
    pass


def stop_and_wait_c():
    # CLIENT
    with open(args.file, 'rb') as file:
        img = file.read()

    data = []
    # Turns the data into a list of elements with length 1460
    for i in range(0, len(img), 1460):
        data.append(img[i:i+1460])

    sequence = 1  # Needed for the first sequence
    body = b''
    flags = 0

    # window and acknowledgement number in the header is always 0 and fixed for the client
    acknowledgment_number = 0
    window = 0

    if args.test == 'skip_seq':
        skip = True  # A skip to be done
        skip_seq = 2  # Skips sequence number 2
    else:
        skip = False
        skip_seq = 0

    # Send the content of the requested file to the server
    while True:
        if sequence <= len(data):
            print(f'\ncreating a packet #{sequence}')
            # Extracts next data-sequence
            body = data[sequence-1]
            # adds a FIN flag if it is the last sequence
            flags = 0 if sequence <= len(data) else 2
        elif sequence > len(data):
            print("\nAll data sent")
            # Returns data size for calculation of throughput value
            return 1460 * len(data)

        print(f'data size = {len(body)}')
        msg = create_packet(sequence, acknowledgment_number, flags, window, body)

        # Skips sequence #2 (skip_seq) if test 1 is active
        if skip and sequence == skip_seq:
            skip = False  # To keep it from skipping multiple times
        else:
            # Send packet and set the timer
            sender_socket.sendto(msg, receiver_address)

            # Set timeout
            sender_socket.settimeout(0.5)

        try:
            # listens for ack from server that the packet has been received
            ack_msg = sender_socket.recv(12)
            seq, ack, flags, win = parse_header(ack_msg)  # it's an ack message with only the header
            SYN, ACK, FIN = parse_flags(flags)

            if ACK:
                print(f"ACK received #{sequence}")
                if sequence == ack:
                    print(f"Correct ACK received #{sequence}")
                    sequence += 1

        except socket.timeout:
            print(f"Timed out: ACK not received - resending packet #{sequence}")
            continue


def stop_and_wait_s():
    # SERVER
    data = []  # Destination for received data, whose length allows for track of progress
    sequence = 0  # Receive progress

    # window and sequence number in the header is always 0 for stop_and_wait and fixed for the server
    sequence_number = 0
    window = 0

    # Test case skip_ack to skip the sending of a specific ack
    if args.test == 'skip_ack':
        skip = True  # A skip to be done
        skip_ack = 4  # Skips ack number 4
    else:
        skip = False
        skip_ack = 0

    # Retrieves all data
    while True:
        msg, sender_address = receiver_socket.recvfrom(1472)
        header_from_msg = msg[:12]
        seq, ack, flags, win = parse_header(header_from_msg)
        print(f'\n\nseq={seq}, ack={ack}, flags={flags}, receiver-window={win}')
        SYN, ACK, FIN = parse_flags(flags)

        if seq > 0:
            if seq == sequence + 1:
                print(f"Correct packet received #{seq}")
                data.append(msg[12:])  # Stores decoded data
                sequence += 1  # Increments progress

            # Preparing ack (DUPACK if previous if-statement wasn't true
            body = b''
            print(f'Creating an acknowledgment packet #{seq}')

            # 0 1 0 0  ack flag set
            flags = 4

            msg = create_packet(sequence_number, sequence, flags, window, body)

            # Skips ack #4 (skip_ack) if the respective test is active triggering a retransmission
            if skip and sequence == skip_ack:
                skip = False  # To keep it from skipping multiple times
                print(f"Skipping ACK #{sequence}")
            else:
                # Sends ack
                receiver_socket.sendto(msg, sender_address)

        elif FIN:
            print("Transfer finished")
            return b''.join(data)


def GBN_c():
    # CLIENT
    with open(args.file, 'rb') as file:
        img = file.read()

    data = []
    # Turns the data into a list of elements with length 1460
    for i in range(0, len(img), 1460):
        data.append(img[i:i+1460])

    sequence = 1  # Needed for the first sequence

    # window and acknoledgement number in the header is fixed for client
    acknowledgment_number = 0
    window = 5

    if args.test == 'skip_seq':
        skip = True  # A skip to be done
        skip_seq = 2  # Skips sequence number 2
    else:
        skip = False
        skip_seq = 0

    # Send the content of the requested file to the server
    while True:
        for i in range(0, window) and sequence <= len(data):
            # Extracts next data-sequence
            body = data[sequence-1+i]
            # adds a FIN flag if it is the last sequence
            flags = 0 if sequence == len(data) else 2

            print(f'data size = {len(body)}')
            msg = create_packet(sequence, acknowledgment_number, flags, window, body)

            # Skips sequence #2 (skip_seq) if test 1 is active
            if skip and sequence == skip_seq:
                skip = False  # To keep it from skipping multiple times
            else:
                # Send packet and set the timer
                sender_socket.sendto(msg, receiver_address)
                # Set timeout
                sender_socket.settimeout(0.5)
        if sequence > len(data):
            print("\nAll data sent")
            # Returns data size for calculation of throughput value
            return 1460 * len(data)

        try:
            for i in range(0, window) and sequence <= len(data):
                # listens for ack from server that the packet has been received
                ack_msg = sender_socket.recv(12)
                seq, ack, flags, win = parse_header(ack_msg)  # it's an ack message with only the header
                SYN, ACK, FIN = parse_flags(flags)

                if ACK:
                    print(f"ACK received #{sequence}")
                    if sequence == ack:
                        print(f"Correct ACK received #{sequence}")
                        sequence += 1
                        if i < window:
                            sender_socket.settimeout(0.5)

        except socket.timeout:
            print(f"Timed out: ACK not received for packet #{sequence}")
            continue


def GBN_s():
    # SERVER
    data = []  # Destination for received data, whose length allows for track of progress
    sequence = 0  # Receive progress

    # Sequence number and window is fixed for GBN
    sequence_number = 0
    window = 0

    # Test case skip_ack to skip the sending of a specific ack
    if args.test == 'skip_ack':
        skip = True  # A skip to be done
        skip_ack = 4  # Skips ack number 4
    else:
        skip = False
        skip_ack = 0

    # Retrieves all data
    while True:
        # Receiving from client
        msg, sender_address = receiver_socket.recvfrom(1472)

        # Parsing the header
        header_from_msg = msg[:12]
        seq, ack, flags, win = parse_header(header_from_msg)
        print(f'\n\nseq={seq}, ack={ack}, flags={flags}, receiver-window={win}')
        SYN, ACK, FIN = parse_flags(flags)

        # The received window size will be used in the code
        if seq > 0:
            if seq == sequence + 1:
                print(f"Correct packet received #{seq}")
                data.append(msg[12:])  # Stores decoded data
                sequence += 1  # Increments progress

            # Preparing ack (DUPACK if previous if-statement wasn't true
            body = b''
            print(f'Creating an acknowledgment packet #{seq}')

            # 0 1 0 0  ack flag set
            flags = 4

            msg = create_packet(sequence_number, sequence, flags, window, body)

            # Skips ack #4 (skip_ack) if the respective test is active triggering a retransmission
            if skip and sequence == skip_ack:
                skip = False  # To keep it from skipping multiple times
                print(f"Skipping ACK #{sequence}")
            else:
                # Sends ack
                receiver_socket.sendto(msg, sender_address)

        elif FIN:
            print("Transfer finished")
            return b''.join(data)


def SR_c():
    pass


def SR_s():
    pass


# Global variables #
check_ip(args.ipaddress)
check_port(args.port)
ip = args.ipaddress
port = args.port

# If using both the --s and the --c flag (and reliability), the system will exit
if args.server and args.client:
    print("Error: you can not run both in server and client mode")
    sys.exit()
# SENDER SOCKET (CLIENT) #
elif args.client:
    # Creating the sender socket and specifying the receiver address
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver_address = (ip, port)

    # ESTABLISHING A CONNECTION FIRST #
    sequence_number = 0
    acknowledgment_number = 0  # an ack for the last sequence
    window = 0  # window value should always be sent from the receiver-side
    body = b''

    # S A F R - SYN ACK FIN RST
    flags = 8  # 1 0 0 0  SYN flag

    # Sends SYN flag to initiate the thee-way handshake
    msg = create_packet(sequence_number, acknowledgment_number, flags, window, body)
    sender_socket.sendto(msg, receiver_address)
    print("SYN sent")

    # Setting timeout
    sender_socket.settimeout(0.5)
    print("Setting timeout: 0.5s")

    try:
        # Try to receive SYN ACK from server
        syn_ack_msg = sender_socket.recv(12)

        # Parsing the header
        seq, ack, flags, win = parse_header(syn_ack_msg)  # SYN ACK -> only header with flags set to: 1 1 0 0
        SYN, ACK, FIN = parse_flags(flags)

        if SYN and ACK:
            print(f"SYN ACK received: flags set: syn-> {SYN}, ack-> {ACK}, fin-> {FIN}")

            sequence_number = 0
            acknowledgment_number = 0  # an ack for the last sequence
            window = 0  # window value should always be sent from the receiver-side
            body = b''

            # S A F R - SYN ACK FIN RST
            flags = 4  # 0 1 0 0  ACK flag
            msg = create_packet(sequence_number, acknowledgment_number, flags, window, body)

            # Sending ACK to confirm an established connection
            sender_socket.sendto(msg, receiver_address)
            print("ACK sent")
            print("Connection established..")
    except socket.timeout:
        print("Timed out: Didn't receive a SYN ACK")
        sys.exit()

    start_time = time.time()
    data_size = 0
    # When a connection is established, the chosen -r argument will start its respective method
    if args.reliability == "stop-and-wait":
        data_size = stop_and_wait_c()
    elif args.reliability == "GBN":
        data_size = GBN_c()
    elif args.reliability == "SR":
        data_size = SR_c()

    # Lapsed time in ms
    lapsed_time = (time.time() - start_time) * 1000
    # Throughput value in Mbps
    throughput = data_size / lapsed_time / 1_000 * 8


    # Closing of the connection
    sequence_number = 0
    acknowledgment_number = 0  # an ack for the last sequence
    window = 0  # window value should always be sent from the receiver-side
    body = b''

    # S A F R - SYN ACK FIN RST
    flags = 2  # 0 0 1 0  FIN flag
    msg = create_packet(sequence_number, acknowledgment_number, flags, window, body)

    # deadline = time.time() + 5000
    # deadline > time.time()
    sender_socket.settimeout(0.5)
    while True:
        try:
            sender_socket.sendto(msg, receiver_address)
            print("FIN sent")

            ack_msg = sender_socket.recv(12)

            # Parsing the header
            seq, ack, flags, win = parse_header(ack_msg)  # ACK -> only header with flags set to: 0 1 0 0
            SYN, ACK, FIN = parse_flags(flags)

            if ACK and ack == 0:
                print(f"ACK received: flags set: syn-> {SYN}, ack-> {ACK}, fin-> {FIN}")
                print(f"\nThroughput value over {lapsed_time:.2f} ms is {throughput:.2f} Mbps")
                print("Shutting down..")
                sender_socket.close()
                sys.exit()
        except socket.timeout:
            print("Timed out: Did not receive a FIN ACK")
            sys.exit()

# RECEIVER SOCKET (SERVER) #
elif args.server:
    # Creating the receiver socket and specifying the receiver address
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Attempting to bind server's port and IP
    try:
        # Start-up
        receiver_socket.bind((ip, port))
        startupMsg = "A server is listening on port " + str(port)

        # Output with dashes
        print("-" * len(startupMsg))
        print(startupMsg)
        print("-" * len(startupMsg))

    # If not, print an exception message and close the program
    except Exception as e:
        print('Bind failed..', e)
        sys.exit()

    # ESTABLISHING CONNECTION #
    while True:
        # Waits for the SYN from client
        try:
            syn_or_ack, sender_address = receiver_socket.recvfrom(12)

            # Parsing the header
            seq, ack, flags, win = parse_header(syn_or_ack)  # SYN -> only header with flags set to: 1 0 0 0
            SYN, ACK, FIN = parse_flags(flags)

            if SYN:
                print(f"SYN received: flags set: syn-> {SYN}, ack-> {ACK}, fin-> {FIN}")

                # Sends SYN ACK
                sequence_number = 0
                acknowledgment_number = 0  # an ack for the last sequence
                window = 0  # window value should always be sent from the receiver-side
                body = b''

                # S A F R - SYN ACK FIN RST
                flags = 12  # 1 1 0 0  SYN ACK flag

                # Sends SYN ACK
                msg = create_packet(sequence_number, acknowledgment_number, flags, window, body)
                receiver_socket.sendto(msg, sender_address)
                #print("Couldn't send SYN ACK")
                receiver_socket.settimeout(0.5)
            elif ACK:
                print("Ready to receive a file!")

                data = ''
                if args.reliability == "stop-and-wait":
                    data = stop_and_wait_s()
                elif args.reliability == "GBN":
                    data = GBN_s()
                elif args.reliability == "SR":
                    data = SR_s()

                with open("picture-recv.gif", "wb") as f:
                    f.write(data)

                if data:
                    # Sends ACK
                    sequence_number = 0
                    acknowledgment_number = 0
                    window = 0
                    body = b''

                    # S A F R - SYN ACK FIN RST
                    flags = 4  # 0 1 0 0 ACK flag

                    msg = create_packet(sequence_number, acknowledgment_number, flags, window, body)
                    receiver_socket.sendto(msg, sender_address)

                    print("ACK sent")
                    receiver_socket.close()
                    sys.exit("Shutting down..")
                    
        except socket.timeout:
            print("Timed out: Did not receive an ACK")
            sys.exit("Shutting down..")

# If neither the -s nor -c flag is specified (except reliability), the system will also exit
else:
    print("Error: you must run either in server or client mode")
    sys.exit()
