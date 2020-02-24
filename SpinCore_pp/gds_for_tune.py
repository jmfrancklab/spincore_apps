from Instruments import *
from pyspecdata import *
import time
from serial.tools.list_ports import comports
import serial
from scipy import signal
import SpinCore_pp
import sys
import threading

default_field = 3504.24 # G -- give this to 2 s.f.!!
default_effective_gamma = 0.0042490577 # MHz/G
field = None
effective_gamma = None
if len(sys.argv) > 1:
    field = float(sys.argv[1])
    assert field > 2500 and field < 4000, "first argument should be a field value!!!"
if len(sys.argv) > 2:
    effective_gamma = float(sys.argv[2])/1e4
    assert effective_gamma > 41 and effective_gamma < 43, "second argument should be effective gamma in MHz/T"
if field is None: field = default_field
if effective_gamma is None: effective_gamma = default_effective_gamma
carrier_frequency = field*effective_gamma

print "Using a field of %f and an effective gamma of %g to predict a frequency of %f MHz"%(field,effective_gamma,carrier_frequency)

fl = figlist_var()

print "These are the instruments available:"
SerialInstrument(None)
print "done printing available instruments"

with GDS_scope() as g:
    g.reset()
    g.CH1.disp=True
    g.CH2.disp=True
    g.write(':CHAN1:DISP ON')
    g.write(':CHAN2:DISP ON')
    g.write(':CHAN3:DISP OFF')
    g.write(':CHAN4:DISP OFF')
    g.CH1.voltscal=100E-3
    g.CH2.voltscal=50E-3
    g.timscal(500e-9, pos=2.325e-6)
    g.write(':CHAN1:IMP 5.0E+1')
    g.write(':CHAN2:IMP 5.0E+1')
    g.write(':TRIG:SOUR CH1') 
    g.write(':TRIG:MOD NORMAL')
    g.write(':TRIG:HLEV 7.5E-2')
def waiting_func():
    for j in range(3):
        time.sleep(3)
        print "counter number %d"%j
def other_func(carrier_frequency):
    for j in range(3):
        time.sleep(3)
        print "second func: counter number %d"%j
def run_tune(carrier_frequency):
    SpinCore_pp.tune(carrier_frequency)
tune_thread = threading.Thread(target=run_tune,
        args=(carrier_frequency,))
display_waiting = threading.Thread(target=waiting_func)
tune_thread.start()
display_waiting.start()
display_waiting.join()
tune_thread.join()
