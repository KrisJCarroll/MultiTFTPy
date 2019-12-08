# tftp_server.py
# Author: Kristopher Carroll
# CSCE A365 - Computer Networks

import socket
import argparse
import threading
import select

class TFTPServer(threading.Thread):
    TERMINATE_LENGTH = 512 + 4 # 512 bytes of data, 4 bytes header = 516 bytes maximum packet size
    ENCODE_MODE = 'netascii' # we're not expected to change this

    # Defining key-value pairs for ascii equivalents of opcodes
    OPCODES = {
        'unknown' : 0,
        'read' : 1,
        'write' : 2,
        'data' : 3,
        'ack' : 4,
        'error' : 5
    }
    # Defining key-value pairs for error codes and their ascii messages
    TFTP_ERRORS = {
        0 : "Undefined error.",
        1 : "File not found.",
        2 : "Access violation.",
        3 : "Disk full or allocation exceeded.",
        4 : "Illegal TFTP operation.",
        5 : "Unknown TID.",
        6 : "File already exists.",
        7 : "No such user.",
    }

    def __init__(self, source_port):
        self.serv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serv_sock.bind(('',source_port))

    def send_ack(packet):
        ack = bytearray(packet[0:4])
        ack[1] = 4 # change opcode to 04
        s.sendto(ack, server)

    # Used to check ACKs during write operations
    # Requires: previously acquired packet in bytes object
    #           expected block number in integer form
    # Returns: integer form of the block number ACK'ed
    # Raises TypeError (generic error) if the packet is not an ACK
    def check_ack(packet, block):
        # turn the requisite data into integers for easier comparison and handling
        opcode = int.from_bytes(packet[0:2], byteorder='big')
        block_num = int.from_bytes(packet[2:4], byteorder='big')
        # packet is an ACK for the expected block number
        if opcode == OPCODES['ack'] and block_num == block:
            return block
        # packet is an ACK
        elif opcode == OPCODES['ack']:
            return block_num
        # packet isn't an ACK, we shouldn't be here, break everything
        else:
            raise TypeError

    # basic method for checking to see if packet is an error packet
    def check_error(packet):
        data = bytearray(packet)
        opcode = data[0:2]
        return int.from_bytes(opcode, byteorder='big') == OPCODES["error"]

    def run(self):
        data = self.serv_sock.recvfrom(1024)
        print(data)
        
        while True:
            read, write, exc = select.select(read_sockets, [], [])

            for socket in read:
                sock, address = self.serv_sock.accept()
                print("Connected to {}".format(address))
                sock.settimeout(2)
                read.append(sock)
    
    def stop(self):
        pass

class Main:

    # Parsing for argument flags
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", required=True, type=int, help="supply server port information")

    args = parser.parse_args()

    # checking for appropriate server port numbers
    if args.sp < 5000 or args.sp > 65535:
        parser.exit(message="\tERROR(args): Server port out of range\n")
    SERVER_PORT = args.sp
    print("Server port:", SERVER_PORT)

    server = TFTPServer(SERVER_PORT).start()
    server.run()