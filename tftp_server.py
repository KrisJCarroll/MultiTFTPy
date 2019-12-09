# tftp_server.py
# Author: Kristopher Carroll
# CSCE A365 - Computer Networks

import socket
import argparse
import threading
import select
import random
import time

class TFTPServer:
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
        threading.Thread.__init__(self)
        self.serv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serv_sock.bind(('',source_port))
        self.serv_sock.setblocking(1)

    def send_ack(self, packet):
        ack = bytearray(packet[0:4])
        ack[1] = 4 # change opcode to 04
        s.sendto(ack, server)

    # Used to check ACKs during write operations
    # Requires: previously acquired packet in bytes object
    #           expected block number in integer form
    # Returns: integer form of the block number ACK'ed
    # Raises TypeError (generic error) if the packet is not an ACK
    def check_ack(self,packet, block):
        # turn the requisite data into integers for easier comparison and handling
        opcode = int.from_bytes(packet[0:2], byteorder='big')
        block_num = int.from_bytes(packet[2:4], byteorder='big')
        # packet is an ACK for the expected block number
        if opcode == TFTPServer.OPCODES['ack'] and block_num == block:
            return block
        # packet is an ACK
        elif opcode == TFTPServer.OPCODES['ack']:
            return block_num
        # packet isn't an ACK, we shouldn't be here, break everything
        else:
            raise TypeError

    # basic method for checking to see if packet is an error packet
    def check_error(packet):
        data = bytearray(packet)
        opcode = data[0:2]
        return int.from_bytes(opcode, byteorder='big') == OPCODES["error"]

    def send_data(self, sock, server, ack, block, data):
        packet = bytearray(ack[0:2])
        packet[1] = 3 # change ACK packet to DATA packet
        # adding block number
        packet += block.to_bytes(2, byteorder='big') # padded to 2 bytes size
        # adding data
        packet += data
        sock.sendto(packet, server)

    def write(self, sock, packet, server, filename):
        file = open(filename, "rb")
        block = 0
        byte_data = file.read()
        while True:
            data = byte_data[block*512 : (block*512) + 512] # get the correct data segment from block number
            block += 1 # increment the block number for next data packet
            self.send_data(sock, server, packet, block, data)
            if len(data) < 512 or block >= 65535:
                break
            packet, address = sock.recvfrom(TFTPServer.TERMINATE_LENGTH)
            block = self.check_ack(packet, block) # get the expected block number by examining ACK
        # all done, clean it up
        file.close()
        sock.close()

    def run(self):
        
        while True:
            read_socks = [self.serv_sock]
            inputs, outputs, exc = select.select(read_socks, [], [])
            for s in inputs:
                if s is self.serv_sock:
                    packet, server = s.recvfrom(1024)
                    new_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                    new_sock.bind(('', random.randint(5000, 65535)))
                    read_socks.append(new_sock)
                    filename = bytearray()
                    byte = packet[2]
                    i = 2
                    while byte != 0:
                        filename.append(byte)
                        i += 1
                        byte = packet[i]
                    filename = filename.decode('ascii')
                    if filename == "shutdown.txt":
                        exit()
                    new_thread = threading.Thread(target=self.write, args=(new_sock, packet, server, filename), daemon=True).start()
            else:
                time.sleep(0.2)
        
        
    
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

    server = TFTPServer(SERVER_PORT)
    server.run()