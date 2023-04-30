import socket
import threading
from struct import *


class DRTP:
    header_format = '!IIHH'

    def __init__(self, ip, port, reliable_method): #Create construtor for drtp with attributes. Also creates socket
        self.ip = ip
        self.port = port
        self.reliable_method = reliable_method
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((ip, port))

    def create_packet(self, seq, ack, flags, win, data): #Method takes inputs and return
        header = pack(self.header_format, seq, ack, flags, win)
        packet = header + data
        return packet

    def parse_header(self, header): # Takes 12-byte header unpacks values and return ack,seq, win and flags
        header_from_msg = unpack(self.header_format, header)
        return header_from_msg

    def parse_flags(self, flags): # Extract value from  3 2 ,1 represent bit positions of syn,ack,flags
        syn = flags & (1 << 3)
        ack = flags & (1 << 2)
        fin = flags & (1 << 1)
        return syn, ack, fin

    def send(self, data, addr):
        pass

    def recv(self, bufsize):
        pass

    def close(self):
        self.socket.close()

    def start_server(self, handler):
        while True:
            data, addr = self.recv(1472)
            handler(data, addr)

    def serve(self, handler):
        server_thread = threading.Thread(target=self.start_server, args=(handler,))
        server_thread.daemon = True #Terminate the code when main program exits
        server_thread.start()
