from pyspecdata import *
import os
import socket
import sys
import time
def API_sender(value):
    IP = "jmfrancklab-bruker.syr.edu"
    if len(sys.argv) > 1:
        IP = sys.argv[1]
    PORT = 6001
    print "target IP:", IP
    print "target port:", PORT
    MESSAGE = str(value)
    print "SETTING FIELD TO...", MESSAGE
    sock = socket.socket(socket.AF_INET, # Internet
            socket.SOCK_STREAM) # TCP
    sock.connect((IP, PORT))
    sock.send(MESSAGE)
    sock.close()
    print "FIELD SET TO...", MESSAGE
    return
B0 = 3409.2 # Determine this from Field Sweep
API_sender(B0)
exit()