'''
    #Utility functions: 1) to create a packet of 1472 bytes with header (12 bytes) (sequence number, acknowledgement number,
    #flags and receiver window) and applicaton data (1460 bytes), and 2) to parse
    # the extracted header from the application data.
'''

from struct import *
import socket
import time
import argparse
import sys
import ipaddress

# ARGUMENT PARSER #
parser = argparse.ArgumentParser(
    prog='simpleperf',
    description='Sends packets between a client and a server')

# Arguments used for the server
parser.add_argument('-s', '--server', action='store_true', help='enable server mode')
parser.add_argument('-b', '--bind', type=str, default='127.0.0.1', help='allows selection of an ip-address')

# Arguments common for both server and client
parser.add_argument('-p', '--port', type=int, default=8088,
                    help='allows selection of a port', metavar='[1024-65535]')
parser.add_argument('-f', '--format', choices=['B', 'KB', 'MB'], default='MB',
                    help='allows changing of the format of the summary')

# Arguments used for the client
parser.add_argument('-c', '--client', action='store_true', help='enable client mode')
parser.add_argument('-I', '--serverip', type=str, default='127.0.0.1',
                    help='allows selection of the servers ip-address')
parser.add_argument('-t', '--time', type=int, choices=range(1, 61), metavar='[1-60]', default=25,
                    help='total duration in seconds for which data should be set')
parser.add_argument('-i', '--interval', type=int, choices=range(1, 30), metavar='[1-30]',
                    help='print stats per z second')
parser.add_argument('-n', '--num', type=str,
                    help='transfer a set number of bytes')

args = parser.parse_args()  # To start the argument parser and its arguments

# SENDER SOCKET (CLIENT) #
sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sender_address = ("127.0.0.2", 1111)
sender_socket.bind(sender_address)

# RECEIVER SOCKET (SERVER) #
receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_address = ("127.0.0.1", 6969)
receiver_socket.bind(receiver_address)

# I integer (unsigned long) = 4bytes and H (unsigned short integer 2 bytes)
# see the struct official page for more info

header_format = '!IIHH'

# print the header size: total = 12
print(f'size of the header = {calcsize(header_format)}')


# A function that checks that the IP-address is valid #
def check_ip(address):
    # Tries to take an IP-address in
    try:
        val = ipaddress.ip_address(address)
        print(f"The IP address {val} is valid.")

    # If it does not work, an error is raised
    except ValueError:
        print(f"The IP address is {address} not valid")


# A function that checks that the port is valid #
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
        print('port cannot be a negative integer')
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
    print(f'packet containing header + data of size {len(packet)}')  # just to show the length of the packet
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


alldata = 'e' * 6000
# Send the content of the requested file to the server
for i in range(0, len(alldata) % 1460):
    sequence_number = 1
    acknowledgment_number = 0
    window = 0  # window value should always be sent from the receiver-side
    flags = 0  # we are not going to set any flags when we send a data packet

    # now let's create a packet with sequence number 1
    print('\n\ncreating a packet')

    data = alldata[(1460 * (sequence_number - 1)):(1460 * sequence_number)]
    print(f'app data for size ={len(data)}')
    # msg now holds a packet, including our custom header and data
    msg = create_packet(sequence_number, acknowledgment_number, flags, window, data)

    deadline = time.time() + 0.5  # deadline in 500ms
    # While loop to assure sending
    while True:
        # send
        sender_socket.sendto(msg, receiver_address)

        try:
            # listens for ack
            ack_msg = sender_socket.recv(12)
            sender_socket.settimeout(0.5)
            seq, ack, flags, win = parse_header(ack_msg)  # it's an ack message with only the header
            # checks for ack
            if ack == sequence_number:
                break
        except TimeoutError as e:
            print(e, "ack timed out")

        print("resending packet")
    sequence_number += 1

# Server
msg = receiver_socket.recv(1472)

# now let's look at the headerL
# we already know that the header is in the first 12 bytes

header_from_msg = msg[:12]
print(len(header_from_msg))

# now we get the header from the parse_header function
# which unpacks the values based on the header_format that
# we specified
seq, ack, flags, win = parse_header(header_from_msg)
print(f'seq={seq}, ack={ack}, flags={flags}, recevier-window={win}')

# let's extract the data_from_msg that holds
# the application data of 1460 bytes
data_from_msg = msg[12:]
print(len(data_from_msg))
print(data.decode())

# let's mimic an acknowledgment packet from the receiver-end
# now let's create a packet with acknowledgment number 1
# an acknowledgment packet from the receiver should have no data
# only the header with acknowledgment number, ack_flag=1, win=6400
data = b''
print('\n\nCreating an acknowledgment packet:')
print(f'this is an empty packet with no data ={len(data)}')

sequence_number = 0
acknowledgment_number = 1  # an ack for the last sequnce
window = 0  # window value should always be sent from the receiver-side

# let's look at the last 4 bits:  S A F R
# 0 0 0 0 represents no flags
# 0 1 0 0  ack flag set, and the decimal equivalent is 4
flags = 4

msg = create_packet(sequence_number, acknowledgment_number, flags, window, data)
print(f'this is an acknowledgment packet of header size={len(msg)}')

# let's parse the header
seq, ack, flags, win = parse_header(msg)  # it's an ack message with only the header
print(f'seq={seq}, ack={ack}, flags={flags}, receiver-window={win}')

# now let's parse the flag field
syn, ack, fin = parse_flags(flags)
