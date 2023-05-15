from struct import *  # To pack and unpack
import ipaddress  # In order to check for valid IP-addresses
import argparse  # In order to utilize arguments
import socket  # Import of socket module
import time  # In order to utilize time
import sys  # In order to terminate the program

# ARGUMENT PARSER #
parser = argparse.ArgumentParser(
    prog='DRTP application',
    description='Transfers a file between a client and a server using DRTP')

# Arguments used for the client/sender
parser.add_argument('-c', '--client', action='store_true', help='enable client mode')
parser.add_argument('-f', '--file', type=str, choices=['picture.jpg', 'safi.jpg'], help='input a file to be sent')

# Arguments used for the server/receiver
parser.add_argument('-s', '--server', action='store_true', help='enable server mode')

# Arguments common for both server and client
parser.add_argument('-p', '--port', type=int, default=8088, help='allows selection of a port', metavar='[1024-65535]')
parser.add_argument('-i', '--ipaddress', type=str, default='127.0.0.1', help='allows selection of an ip-address')
parser.add_argument('-r', '--reliability', choices=['stop-and-wait', 'GBN', 'SR'], required=True,
                    help='allows selection of different reliability functions')
parser.add_argument('-t', '--test', type=str, choices=['skip_ack', 'skip_seq', 'send_old'],
                    help='selection of which test case to run')

args = parser.parse_args()  # Start the argument parser and its arguments

################
# MAIN PROGRAM #
################

# GLOBAL VARIABLES #
header_format = '!IIHH'
rtt = 0.125  # Default rtt (sets time-outs to 500 ms)


# FUNCTIONS #

# Helper functions #
# A function that checks if the IP-address is valid
def check_ip(address):
    # Takes an IP-address in
    try:
        # IP-address is valid
        val = ipaddress.ip_address(address)
        # print(f"The IP address {val} is valid.")

    # If it does not work, an error is raised
    except ValueError:
        print(f"The IP address is {address} not valid")
        sys.exit()


# A function that checks if the port is valid
def check_port(val):
    # Tries to take a port in, and casts it to an integer
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


# A function which creates a packet (data and header - 1472 bytes)
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
    # print(f'packet containing header + data of size {len(packet)}')  # to show the length of the packet
    return packet


# A function that parses/unpacks a header
def parse_header(header):
    # taks a header of 12 bytes as an argument,
    # unpacks the value based on the specified header_format
    # and return a tuple with the values
    header_from_msg = unpack(header_format, header)
    # parse_flags(flags)
    return header_from_msg


# A function that parses/unpacks flags
def parse_flags(flags):
    # we only parse the first 3 fields because we're not
    # using rst in our implementation
    syn = flags & (1 << 3)
    ack = flags & (1 << 2)
    fin = flags & (1 << 1)
    return syn, ack, fin


# Main functions #

# Stop-and-wait (client)
def stop_and_wait_c():
    # CLIENT
    data = []
    sequence = 1  # Needed for the first sequence
    body = b''
    flags = 0
    rtt = 0.125

    with open(args.file, 'rb') as file:
        img = file.read()

    # Turns the data into a list of elements with length 1460
    for i in range(0, len(img), 1460):
        data.append(img[i:i + 1460])

    # Test case skip_seq
    if args.test == 'skip_seq':
        skip = True  # A skip to be done
        skip_seq = 2410  # Skips sequence number 2410
    else:
        skip = False
        skip_seq = 0

    # Test case send_old
    if args.test == 'send_old':
        send_old = True  # Old sequence is to be sent
        old_seq = 2410  # When old sequence will be sent
    else:
        send_old = False
        old_seq = 0

    # Send the content of the requested file to the server
    while True:
        if sequence <= len(data):
            print(f'\ncreating a packet #{sequence}')
            # Extracts next data-sequence
            body = data[sequence - 1]
            # adds a FIN flag if it is the last sequence
            flags = 0 if sequence <= len(data) else 2
        elif sequence > len(data):
            print("\nAll data sent")
            # Returns data size for calculation of throughput value
            return 1460 * len(data)

        print(f'data size = {len(body)}')
        # Acknowledgement number and window are fixed and static for the client
        msg = create_packet(sequence, 0, flags, 0, body)
        """
        # Starts measuring RTT before sending of packet
        rtt_start_time = time.time()
        rtt_start_seq = sequence
        """
        # Skips sequence #2 (skip_seq) if test 1 is active
        if skip and sequence == skip_seq:
            skip = False  # To keep it from skipping multiple times
            print("Packet sending skipped")
        # Sends an old sequence #2 as test case after sending packet #2410 (same data, but different header)
        elif send_old and sequence == old_seq:
            send_old = False  # To keep it from skipping multiple times
            msg = create_packet(2, 0, flags, 0, body)
            sender_socket.sendto(msg, receiver_address)
            print("Old sequence sent")
        else:
            # Send packet
            sender_socket.sendto(msg, receiver_address)

        # Sets timeout
        sender_socket.settimeout(4 * rtt)
        try:
            # listens for ack from server that the packet has been received
            ack_msg = sender_socket.recv(12)
            seq, ack, flags, win = parse_header(ack_msg)  # it's an ack message with only the header
            SYN, ACK, FIN = parse_flags(flags)
            """
            # Sets rtt if correct packet is received
            if rtt_start_seq == ack:
                rtt = time.time() - rtt_start_time
                print(f"RTT: {(rtt * 1000):.2f} ms")
            """
            if ACK:
                if sequence == ack:
                    print(f"Correct ACK received #{sequence}")
                    sequence += 1
                else:
                    print("Wrong ACK received")

        except socket.timeout:
            print(f"Timed out: ACK not received - resending packet #{sequence}")
            continue


# Server function for both stop-and-wait and GBN
def reactive_server():
    # SERVER - used for stop-and-wait() and GBN()
    data = []  # Destination for received data, whose length allows for track of progress
    sequence = 0  # Receive progress

    # Test case skip_ack to skip the sending of a specific ack
    if args.test == 'skip_ack':
        skip = True  # A skip to be done
        skip_ack = 2410  # Skips ack number 4
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
        print(f'\nseq={seq}, ack={ack}, flags={flags}, receiver-window={win}')
        SYN, ACK, FIN = parse_flags(flags)

        if seq > 0:
            if seq == sequence + 1:
                print(f"Correct packet received #{seq}")
                data.append(msg[12:])  # Stores decoded data
                sequence += 1  # Increments progress

            # Sequence number, flags, window, and body are fixed for the server
            msg = create_packet(0, sequence, 4, 0, b'')

            # Skips ack #4 (skip_ack) if the respective test is active triggering a retransmission
            if skip and sequence == skip_ack:
                skip = False  # To keep it from skipping multiple times
                print(f"Skipping ACK #{sequence}")
            else:
                # Sends ack
                print(f'Sending acknowledgment packet #{sequence}')
                receiver_socket.sendto(msg, sender_address)

        elif FIN:
            print("Transfer finished")
            return b''.join(data)  # Joins data from array and returns it


# Go-Back-N (client)
def GBN_c():
    # CLIENT
    data = []  # In order to store the data
    sequence = 1  # Needed for the first sequence
    window = 5  # Window is fixed

    with open(args.file, 'rb') as file:
        img = file.read()

    # Turns the data into a list of elements with length 1460
    for i in range(0, len(img), 1460):
        data.append(img[i:i + 1460])

    # Initialising for test case skip_seq
    if args.test == 'skip_seq':
        skip = True  # A skip to be done
        skip_seq = 2400  # Skips sequence number n
    else:
        skip = False
        skip_seq = 0

    # Send the content of the requested file to the server
    while True:
        print(f"\nCreating {window} packets")
        for i in range(0, window):
            print(f"Creating window-packet #{i + 1}")
            if sequence + i > len(data):
                break
            # Extracts next data-sequence
            body = data[sequence - 1 + i]
            # adds a FIN flag if it is the last sequence
            flags = 0 if sequence <= len(data) else 2
            # Acknowledgement number and window in the header are fixed and static for the client
            msg = create_packet(sequence, 0, flags, 0, body)

            # Skips sequence #2 (skip_seq) if test 1 is active
            if skip and sequence == skip_seq:
                skip = False  # To keep it from skipping multiple times
            else:
                # Send packet and set the timeout
                sender_socket.sendto(msg, receiver_address)

            sender_socket.settimeout(4 * rtt)
        print()
        try:
            while True:
                # Listens for ack from server that the packet has been received
                ack_msg = sender_socket.recv(12)
                seq, ack, flags, win = parse_header(ack_msg)  # it's an ack message with only the header
                SYN, ACK, FIN = parse_flags(flags)

                if ACK and sequence == ack:
                    print(f"Correct ACK received #{sequence}")
                    sequence += 1
                    # All data sent and all ACKs are received - Transfer is done
                    if sequence > len(data):
                        print("\nAll data sent")
                        # Returns data size for calculation of throughput value
                        return 1460 * len(data)

                    # Extracts next data-sequence
                    body = data[sequence - 1]

                    # adds a FIN flag if it is the last sequence
                    flags = 0 if sequence <= len(data) else 2
                    msg = create_packet(sequence, 0, flags, 0, body)

                    # Skips sequence #skip_seq (skip_seq) if test 1 is active
                    if skip and sequence == skip_seq:
                        skip = False  # To keep it from skipping multiple times
                    else:
                        # Send packet
                        sender_socket.sendto(msg, receiver_address)

                    # Sets timeout
                    sender_socket.settimeout(4 * rtt)

        except socket.timeout:
            print(f"\nTimed out: ACK not received for packet #{sequence}")
            continue


# Selective repeat (client)
def SR_c():
    # CLIENT
    data = []  # In order to store the data
    sequence = 1  # Needed for the first sequence
    window = 5  # Window is fixed
    frame = [False] * window  # Frame to keep track of acked sequences within the window

    with open(args.file, 'rb') as file:
        img = file.read()

    # Turns the data into a list of elements with length 1460
    for i in range(0, len(img), 1460):
        data.append(img[i:i + 1460])

    # Initialising for test case skip_seq
    if args.test == 'skip_seq':
        skip = True  # A skip to be done
        skip_seq = 2400  # Skips sequence number n
    else:
        skip = False
        skip_seq = 0

        # Send the content of the requested file to the server
        # while True:
        print(f"\nCreating {window} packets")
        for i in range(0, window):
            print(f"Creating window-packet #{i + 1}")
            if sequence + i > len(data):
                break
            # Signals that an ack is missing
            frame[i] = False
            # Extracts next data-sequence
            body = data[sequence - 1 + i]
            # adds a FIN flag if it is the last sequence
            flags = 0 if sequence <= len(data) else 2
            # Acknowledgement number and window in the header are fixed and static for the client
            msg = create_packet(sequence + i, 0, flags, 0, body)

            # Skips sequence #2 (skip_seq) if test 1 is active
            if skip and sequence == skip_seq:
                skip = False  # To keep it from skipping multiple times
            else:
                # Send packet and set the timeout
                sender_socket.sendto(msg, receiver_address)

            sender_socket.settimeout(4 * rtt)

        while True:
            try:
                # Listens for ack from server that the packet has been received
                ack_msg = sender_socket.recv(12)
                seq, ack, flags, win = parse_header(ack_msg)  # it's an ack message with only the header
                SYN, ACK, FIN = parse_flags(flags)

                # Stores ack if it is within the window
                if ACK and sequence <= ack and sequence + window > ack:
                    print(f"Correct ACK received #{ack} - Frame #{(ack - sequence)}")
                    # Stores ack within the frame
                    frame[ack - sequence] = True
                # Moves the window and sends the last element after each move
                while frame[0]:
                    print("window moves - sends packet")
                    frame.pop(0)
                    frame.append(False)
                    sequence += 1
                    # All data sent and all ACKs are received - Transfer is done
                    if sequence + 1 > len(data):
                        print("\nAll data sent")
                        # Returns data size for calculation of throughput value
                        return 1460 * len(data)
                    # if sequence + window > len(data):
                    # window -= 1
                    # adds a FIN flag if it is the last sequence
                    flags = 0 if sequence <= len(data) else 2
                    # Extracts next data-sequence
                    if sequence - 1 + window < len(data):  # Checks if the index is less than the length of data
                        body = data[sequence - 1 + window]
                        msg = create_packet(sequence + window - 1, 0, flags, 0, body)
                    else:
                        break  # Breaks at the end of data

                    # Skips sequence #skip_seq (skip_seq) if test 1 is active
                    if skip and sequence == skip_seq:
                        skip = False  # To keep it from skipping multiple times
                    else:
                        # Send packet
                        sender_socket.sendto(msg, receiver_address)

                    # Sets timeout
                    sender_socket.settimeout(4 * rtt)

            except socket.timeout:
                print(f"\nTimed out: ACK not received for packet #{sequence}")
                continue


# Selective repeat (server)
def SR_s():
    # SERVER - Selective Repeat
    data = []  # Destination for received data, whose length allows for track of progress
    sequence = 0  # Receive progress
    window = 5
    frame = [None] * window

    # Test case skip_ack to skip the sending of a specific ack
    if args.test == 'skip_ack':
        skip = True  # A skip to be done
        skip_ack = 2410  # Skips ack number 4
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
        print(f'\nseq={seq}, ack={ack}, flags={flags}, receiver-window={win}')
        SYN, ACK, FIN = parse_flags(flags)

        if seq > 0:
            if seq >= sequence + 1 and seq < sequence + window + 1:
                print(f"Correct packet received #{seq}")
                frame[seq - sequence - 1] = msg[12:]  # Buffers decoded data
                # Moves the window and stores buffered data
                while frame[0]:
                    print("window moves - sends ACK")
                    data.append(frame.pop(0))  # Pops from buffer frame into storage
                    frame.append(None)
                    sequence += 1

            # Sequence number, flags, window, and body are fixed for the server
            msg = create_packet(0, seq, 4, 0, b'')

            # Skips ack #4 (skip_ack) if the respective test is active triggering a retransmission
            if skip and sequence == skip_ack:
                skip = False  # To keep it from skipping multiple times
                print(f"Skipping ACK #{sequence}")
            else:
                # Sends ack
                print(f'Sending acknowledgment packet #{seq}')
                receiver_socket.sendto(msg, sender_address)

        elif FIN:
            print("Transfer finished")
            return b''.join(data)  # Joins data from array and returns it


# Variables used for invoking the server/client #
check_ip(args.ipaddress)
check_port(args.port)
ip = args.ipaddress
port = args.port

# If using both the --s and the --c flag (AND reliability), the system will exit
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
    sender_socket.settimeout(4 * rtt)
    print("Setting timeout: 4RTTs")

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

    sender_socket.settimeout(4 * rtt)
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
                print(f"\nElapsed time: {lapsed_time:.2f}ms")
                print(f"Throughput: {throughput:.2f}Mbps")
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
                print("SYN ACK sent")
                receiver_socket.settimeout(4 * rtt)
            elif ACK:
                print("Ready to receive a file!")

                data = ''
                if args.reliability != "SR":
                    data = reactive_server()
                else:
                    data = SR_s()

                dest_name = 'picture-recv.jpg' if args.file == 'picture.jpg' else 'safi-recv.jpg'
                with open(dest_name, "wb") as f:
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
