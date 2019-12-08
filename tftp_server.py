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
        threading.Thread.__init__(self)
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
        data, address = self.serv_sock.recvfrom(1024)
        filename = bytearray()
        byte = data[2]
        i = 2
        while byte != 0:
            filename.append(byte)
            i += 1
            byte = data[i]
        filename = filename.decode('ascii')
        file = open(filename, "wb")
        size = 0 # counter for total size of data received (does not include header size)
        timeouts = 0 # counter for monitoring timeouts
        block = 1 # counter for monitoring block number
        while timeouts < 5:
            try:
                packet, address = self.serf_sock.recvfrom(TERMINATE_LENGTH)
                size += len(packet[4:])
                # check for error packet and handle it if found
                if check_error(packet):
                    errno = int.from_bytes(packet[2:4], byteorder='big')
                    print("ERROR(server): ERRNO[{}] MESSAGE = {}".format(errno, TFTP_ERRORS[errno]))
                    return False
                # block number is as expected, write the next data packet and send it
                if int.from_bytes(packet[2:4], byteorder='big') == block:
                    timeouts = 0
                    block += 1
                    send_ack(packet)
                    data = packet[4:] # grab the data
                    file.write(data)
                # Got a packet for the wrong block number, treat it as a timeout event
                # reconstruct an ACK for the last correct data packet received
                else:
                    timeouts += 1
                    old_packet = bytearray(packet[0:2])
                    old_packet += block.to_bytes(2, byteorder='big')
                    send_ack(packet)

                if len(packet) < TERMINATE_LENGTH:
                    break
            # got a timeout, resend ACK
            except socket.timeout:
                send_ack(packet)
                timeouts += 1
            except:
                print("Connection with server closed.")
                break
        
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

    server = TFTPServer(SERVER_PORT)
    server.start()
    server.run()