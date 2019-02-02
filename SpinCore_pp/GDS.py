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

def collect(date,id_string,captures):
    cap_len = len(captures)
    datalist = []
    print "about to load GDS"
    with GDS_scope() as g:
        print "loaded GDS"
        for x in xrange(1,cap_len+1):
            if x == 1:
                wait = wait_time()
            else:
                time.sleep(wait)
            print "entering capture",x
            ch1_waveform = g.waveform(ch=1)
            ch2_waveform = g.waveform(ch=2)
            data = concat([ch1_waveform,ch2_waveform],'ch').reorder('t')
            if x == 1:
                channels = ((ndshape(data)) + ('capture',cap_len)).alloc()
                channels.setaxis('t',data.getaxis('t')).set_units('t','s')
                channels.setaxis('ch',data.getaxis('ch'))
            channels['capture',x-1] = data
    # {{{ in case it pulled from an inactive channel
    if not isfinite(data.getaxis('t')[0]):
        j = 0
        while not isfinite(data.getaxis('t')[0]):
            data.setaxis('t',datalist[j].getaxis('t'))
            j+=1
            if j == len(datalist):
                raise ValueError("None of the time axes returned by the scope are finite, which probably means no traces are active??")
    # }}}
    s = channels
    s.labels('capture',captures)
    s.name('accumulated_'+date)
    s.hdf5_write(date+'_'+id_string+'.h5')
    print "name of data",s.name()
    print "units should be",s.get_units('t')
    print "shape of data",ndshape(s)
    return

date = '190201'
id_string = 'SpinCore_pulses'
captures = linspace(1,30,30)
collect(date,id_string,captures)
