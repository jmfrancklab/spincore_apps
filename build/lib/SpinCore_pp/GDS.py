from Instruments import GDS_scope
from pyspecdata import *
import time
from timeit import default_timer as timer
#from serial.tools.list_ports import comports
#import serial
from scipy import signal

fl = figlist_var()
    
def wait_time():
    start = time.time()
    print "Waiting for user"
    raw_input()
    return time.time() - start

def collect(date,id_string,captures,wait):
    cap_len = len(captures)
    datalist = []
    print "about to load GDS"
    with GDS_scope() as g:
        print "loaded GDS"
        for x in xrange(1,cap_len+1):
            print "entering capture",x
            print "AWAITING USER"
            raw_input()
            ch1_waveform = g.waveform(ch=1)
            ch2_waveform = g.waveform(ch=2)
            data = concat([ch1_waveform,ch2_waveform],'ch').reorder('t')
            if x == 1:
                channels = ((ndshape(data)) + ('capture',cap_len)).alloc()
                channels.setaxis('t',data.getaxis('t')).set_units('t','s')
                channels.setaxis('ch',data.getaxis('ch'))
            channels['capture',x-1] = data
    s = channels
    s.labels('capture',captures)
    s.name('accumulated_'+date)
    s.hdf5_write(date+'_'+id_string+'.h5')
    print "name of data",s.name()
    print "units should be",s.get_units('t')
    print "shape of data",ndshape(s)
    return

date = '190220'
id_string = 'tunematch'
captures = linspace(1,5,5)
collect(date,id_string,captures,1.5)

