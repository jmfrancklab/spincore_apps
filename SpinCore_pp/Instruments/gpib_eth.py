import socket
import time
from pylab import *

class gpib_eth (object):
    """WARNING: I modified the names of this file and the classes to make it
    less ambiguous -- this probably breaks a lot of stuff -- see the
    appropriate git commit"""
    def __init__(self, ip="jmfrancklab-prologix.syr.edu", port=1234):
        # Switch for OS X
        self.flags = {}
        self.open()
    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()
        return
    def open(self, ip="jmfrancklab-prologix.syr.edu", port=1234):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        try:
            self.socket.connect((ip,port))
        except:
            raise ValueError("Can't connect to port "+str(port)+" on "+ip)
        # here I don't set a timeout, since that seems to demand that we receive everything in the buffer
        self.socket.send('++mode 1'+"\r")
        self.socket.send('++ifc'+"\r")
        self.socket.send('++auto 0'+"\r")
        self.socket.send('++eoi 0'+"\r")
        self.socket.send("++ver\r")
        versionstring = self.socket.recv(1000)
        self.caddr = -1
        if versionstring[0:8]=='Prologix':
            print 'connected to: ',versionstring
        else:
            print 'Error! can\'t find prologix on %s:%d'%(ip,port)
            raise
    def close(self):
        self.socket.close()
    def setaddr(self,addr):
        if(self.caddr != addr):
            self.socket.send('++addr '+str(addr)+"\r")
            self.caddr=addr
    def readandchop(self,addr): # unique to the ethernet one
        retval = self.socket.recv(1024) # get rid of dos newline
        while (retval[-1] == '\r') or (retval[-1] == '\n'): # there should be a function for this (i.e. chop, etc)!
            retval = retval[:-1]
        return retval
    def readline(self,addr):    
        self.setaddr(addr)
        self.socket.send('++read 10'+"\r")
        return self.readandchop(addr)
    def read(self,addr):
        self.setaddr(addr)
        self.socket.send('++read eoi'+"\r")
        return self.readandchop(addr)
    def write(self,addr,gpibstr):
        self.setaddr(addr)
        print "about to send:",gpibstr,"to address",addr
        self.socket.send(gpibstr+"\r")
    def respond(self,addr,gpibstr,printstr):
        self.write(addr,gpibstr)
        print printstr % self.read(addr)
        
    #{{{ Functions for Newer Tek Scope
    def tek_query_var(self,addr,varname):
        self.write(addr,varname+'?')
        temp = self.read(addr)
        temp = temp[len(varname)+2:-1] # remove initial space and trailing \n
        if temp[0]=='\"':
            return temp[1:-1]
        else:
            return double(temp)
    def tek_get_curve(self,addr):
        y_unit = self.tek_query_var(addr,'WFMP:YUN')
        y_mult = self.tek_query_var(addr,'WFMP:YMU')
        y_offset = self.tek_query_var(addr,'WFMP:YOF')
        dx = self.tek_query_var(addr,'WFMP:XIN')
        x_unit = self.tek_query_var(addr,'WFMP:XUN')
        #print y_mult,y_unit,y_offset,dx,x_unit
        self.write(addr,'CURV?')
        self.serial.write('++addr '+str(addr)+"\r")
        time.sleep(0.1)
        self.serial.write('++read eoi'+"\r")
        header_string = self.serial.read(8)
        print "'"+header_string+"'\n"
        print "reading length of length: "+header_string[-1]
        curve_length = self.serial.read(int(header_string[-1]))
        print "reading curve of length: "+curve_length
        x = header_string[0:int(curve_length)]*dx
        return (x_unit,
                y_unit,
                x,
                y_offset+y_mult*array(
                unpack(
                    '%sb'%curve_length,
                    self.serial.read(int(curve_length))
                    )))
    #}}}
    
    #{{{ Functions for HP 54110D Digitizing Oscilloscope
    def hp_get_curve(self,addr):
        # Acquire waveform
        self.write(addr,":acquire:type normal")
        self.write(addr,":digitize CHANNEL2")
        self.write(addr,":waveform:source 2")
        self.write(addr,":waveform:format ascii")
        
        self.write(addr,":waveform:data?");
        
        self.write(addr,"++read eoi");
        wfrm = [int(x) for x in self.serial.readlines()]
        
        # Acquire preamble
        self.write(addr,":waveform:preamble?")
        self.write(addr,"++read eoi");
        pra = self.serial.readline().split(",")
        print 'pra=\'',pra,'\''
        try:
            format = int(pra[0])
            type = int(pra[1])
            points = int(pra[2])
            count = int(pra[3])
        
            xinc = float(pra[4])
            xorig = float(pra[5])
            xref = int(pra[6])
        
            yinc = float(pra[7])
            yorig = float(pra[8])
            yref = int(pra[9])
        
        except IndexError:
            print "Bad preamble recieved"
            exit(1)
        
        if points != len(wfrm):
            print "WARNING: Received less points than specified in the preamble"
        
        x = ((r_[0:len(wfrm)]-xref)*xinc)+xorig
        y = ((array(wfrm)-yref)*yinc)+yorig
        
        # FIXME: No idea what x_unit and y_unit are for. They just get stowed
        #        in the matlab file so for now it's okay. /eazg
        return (1,1,x,y)
    #}}}
