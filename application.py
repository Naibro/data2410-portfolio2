'''
    #Utility functions: 1) to create a packet of 1472 bytes with header (12 bytes) (sequence number, acknowledgement number,
    #flags and receiver window) and applicaton data (1460 bytes), and 2) to parse
    # the extracted header from the application data.

    Qs:
    Should the test-cases be 3 larger test-cases including multiple smaller tests? (e.g. -t 1 will . . .
'''

from struct import *
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
parser.add_argument('-f', '--file', type=str, help='input a file to be sent')

# Arguments used for the server/receiver
parser.add_argument('-s', '--server', action='store_true', help='enable server mode')

# Arguments common for both server and client
parser.add_argument('-p', '--port', type=int, default=8088, help='allows selection of a port', metavar='[1024-65535]')
parser.add_argument('-i', '--ipaddress', type=str, default='127.0.0.1', help='allows selection of an ip-address')
parser.add_argument('-r', '--reliability', choices=['stop-and-wait', 'GBN', 'SR'], required=True,
                    help='allows selection of different reliability functions')
parser.add_argument('-t', '--test_case', type=str, choices=['1', '2', '3'],
                    help='selection of which test case to run')

args = parser.parse_args()  # Start the argument parser and its arguments

# MAIN PROGRAM #

# I integer (unsigned long) = 4bytes and H (unsigned short integer 2 bytes)
# see the struct official page for more info

header_format = '!IIHH'


# print the header size: total = 12
# print(f'size of the header = {calcsize(header_format)}')


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
    #print(f'packet containing header + data of size {len(packet)}')  # just to show the length of the packet
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
    # syn = flags & (1 << 3)
    # ack = flags & (1 << 2)
    # fin = flags & (1 << 1)
    syn = flags // 8
    ack = flags % 8 // 4
    fin = flags % 4 // 2
    return syn, ack, fin


def send_format(file, seq):
    pass


def stop_and_wait_c():
    # CLIENT
    alldata = b'e' * 6344
    # Send the content of the requested file to the server
    for i in range(0, len(alldata) % 1460):
        sequence_number = 1
        acknowledgment_number = 0
        flags = 0  # we are not going to set any flags when we send a data packet
        window = 0  # window value should always be sent from the receiver-side

        # creates a packet with sequence number 1
        print('\n\ncreating a packet')
        body = alldata[:1460]
        print(f'app data for size ={len(body)}')
        # msg now holds a packet, including our custom header and data
        msg = create_packet(sequence_number, acknowledgment_number, flags, window, body)

        # While loop to assure sending
        while True:
            if len(alldata) / 1460 > 1:
                body = alldata[(1460 * (sequence_number - 1)):(1460 * sequence_number)]
            # Last sequence
            else:
                body = alldata[(1460 * (sequence_number - 1)):]
                flags = 2
                print("Last sequence!")

            # Send packet and set the timer
            sender_socket.sendto(msg, receiver_address)
            sender_socket.settimeout(0.5)

            try:
                # listens for ack from server that the packet has been recevied
                ack_msg = sender_socket.recv(12)
                seq, ack, flags, win = parse_header(ack_msg)  # it's an ack message with only the header

                ack = sequence_number

            except ConnectionError as e:
                print(e, "ack timed out")


def stop_and_wait_s():
    """
        Sudo code

        while true
            receive packet
            if match with progress
                store data
                send ack
            else
                send ack of progress
    """
    # SERVER
    data = []  # Destination for received data, whose length allows for track of progress
    sequence = 0  # Receive progress

    # Retrieves all data
    while True:
        msg, sender_address = receiver_socket.recvfrom(1472)
        header_from_msg = msg[:12]
        seq, ack, flags, win = parse_header(header_from_msg)
        print(f'seq={seq}, ack={ack}, flags={flags}, recevier-window={win}')
        SYN, ACK, FIN = parse_flags(flags)

        if ACK:
            if seq == sequence + 1:
                data.append(msg[12:].decode())  # Stores decoded data
                sequence += 1  # Increments progress
            # Preparing ack (repeats ack if previous if-statement wasn't true
            body = b''
            print('\n\nCreating an acknowledgment packet:')
            print(f'this is an empty packet with no data ={len(body)}')

            sequence_number = 0
            acknowledgment_number = sequence  # an ack for the last sequnce
            window = 0  # window value should always be sent from the receiver-side

            # 0 1 0 0  ack flag set
            flags = 4

            msg = create_packet(sequence_number, acknowledgment_number, flags, window, body)
            print(f'this is an acknowledgment packet of header size={len(msg)}')

            receiver_socket.sendto(msg, sender_address)
        elif FIN:
            # Preparing FIN ACK
            body = b''
            sequence_number = 0
            acknowledgment_number = 1
            window = 0

            # 0 1 1 0
            flags = 6

            msg = create_packet(sequence_number, acknowledgment_number, flags, window, body)

            print('Sends FIN ACK and closes connection')
            # Sends the FIN ACK, compresses data, and closes connection
            receiver_socket.sendto(msg, sender_address)
            data = data.join('')
            receiver_socket.close()


def GBN_c():
    pass


def GBN_s():
    pass


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
    sender_socket.settimeout(1)
    print("Setting timeout..")

    try:
        # Try to receive SYN ACK from server
        syn_ack_msg = sender_socket.recv(12)

        # Parsing the header
        seq, ack, flags, win = parse_header(syn_ack_msg)  # SYN ACK -> only header with flags set to: 1 1 0 0
        SYN, ACK, FIN = parse_flags(flags)

        if SYN == 1 and ACK == 1:
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
        else:
            print("Something was received, but it was not SYN ACK", syn_ack_msg)
            sys.exit()
    except Exception as e:
        print("Didn't receive a SYN ACK", e)
        sys.exit()

    # When a connection is established, the chosen -r argument will start its respective method
    if args.reliability == "stop-and-wait":
        stop_and_wait_c()
    elif args.reliability == "GBN":
        GBN_c()
    elif args.reliability == "SR":
        SR_c()
    #Fjerne hele else-statementen?
    else:
        print("Du er god hvis du greier å komme hit. Faen meg skriv en metode")

    # Closing of the connection
    sequence_number = 0
    acknowledgment_number = 0  # an ack for the last sequence
    window = 0  # window value should always be sent from the receiver-side
    body = b''

    # S A F R - SYN ACK FIN RST
    flags = 2  # 0 0 1 0  FIN flag
    msg = create_packet(sequence_number, acknowledgment_number, flags, window, body)
    sender_socket.sendto(msg, receiver_address)
    print("FIN sent")

    ack, sender_address = sender_socket.recvfrom(12)

    # Parsing the header
    seq, ack, flags, win = parse_header(ack)  # ACK -> only header with flags set to: 0 1 0 0
    SYN, ACK, FIN = parse_flags(flags)

    if ACK == 1:
        print(f"ACK received: flags set: syn-> {SYN}, ack-> {ACK}, fin-> {FIN}")
        print("Shutting down..")
        sender_socket.close()
        sys.exit()
    else:
        print("Something was received, but it was not an ACK:", ACK)
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
        syn_or_ack, sender_address = receiver_socket.recvfrom(12)

        # Parsing the header
        seq, ack, flags, win = parse_header(syn_or_ack)  # SYN -> only header with flags set to: 1 0 0 0
        SYN, ACK, FIN = parse_flags(flags)

        if SYN == 1:
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
        elif ACK == 1:
            print(f"ACK received: flags set: syn-> {SYN}, ack-> {ACK}, fin-> {FIN}")
            print("Ready to receive a file!")

            if args.reliability == "stop-and-wait":
                stop_and_wait_s()
            elif args.reliability == "GBN":
                GBN_s()
            elif args.reliability == "SR":
                SR_s()
            # Fjerne hele else-statementen?
            else:
                print("Du er god hvis du greier å komme hit. Faen meg skriv en metode")

            # Closing the connection
            fin_msg, sender_address = receiver_socket.recvfrom(12)

            # Parsing the header
            seq, ack, flags, win = parse_header(fin_msg)  # FIN -> only header with flags set to: 0 0 1 0
            SYN, ACK, FIN = parse_flags(flags)

            if FIN == 1:
                print(f"FIN msg received: flags set: syn-> {SYN}, ack-> {ACK}, fin-> {FIN}")

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
                print("Shutting down..")
                receiver_socket.close()
                sys.exit()
        else:
            print("Something was received, but it was not an ACK", syn_or_ack)
            sys.exit()

# If neither the -s nor -c flag is specified (except reliability), the system will also exit
else:
    print("Error: you must run either in server or client mode")
    sys.exit()
