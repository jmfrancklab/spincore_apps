from Instruments import *
from pyspecdata import *
import time
from serial.tools.list_ports import comports
import serial
from scipy import signal
import SpinCore_pp
import sys
import threading
from pyspecdata import *

default_field = 3505.8 #3506.4 # G -- give this to 2 s.f.!!
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

print("Using a field of %f and an effective gamma of %g to predict a frequency of %f MHz"%(field,effective_gamma,carrier_frequency))
print("")
input("Please note I'm going to assume the control is hooked up to CH1 of the GDS and the reflection is hooked up to CH2 of the GDS... (press enter to continue)")

fl = figlist_var()

print("These are the instruments available:")
SerialInstrument(None)
print("done printing available instruments")
def grab_waveforms(g):
    # {{{ capture a "successful" waveform
    ch1 = g.waveform(ch=1)
    ch2 = g.waveform(ch=2)
    success = False
    for j in range(10):
        if ch1.data.max() < 50e-3:
            ch1 = g.waveform(ch=1)
            ch2 = g.waveform(ch=2)
        else:
            success = True
    if not success:
        raise ValueError("can't seem to get a waveform that's large enough!")
    # }}}
    d = concat([ch1,ch2],'ch')
    d.reorder('ch')
    return d
def waiting_func():
    for j in range(3):
        time.sleep(3)
        print("counter number %d"%j)
def other_func(carrier_frequency):
    for j in range(3):
        time.sleep(3)
        print("second func: counter number %d"%j)
def run_tune(carrier_frequency):
    SpinCore_pp.tune(carrier_frequency)

with GDS_scope() as g:
    tune_thread = threading.Thread(target=run_tune,
            args=(carrier_frequency,))
    tune_thread.start()
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
    tune_thread.join()
    d = grab_waveforms(g)
    d_orig = d.C
    d.ft('t',shift=True)
    d['t':(carrier_frequency*2.3e6,None)] = 0
    d['t':(None,0)] = 0
    d *= 2
    d.ift('t')
    flat_slice = d['t':(3.7e-6,6.5e-6)]# will always be the same since the scope settings are the same
with figlist_var() as fl:
    #d['ch',1] *= sqrt(2) # I'm only observing 1/2 of the power of the reflection (so 1/sqrt(2) of the voltage)
    d['ch',1] *= 2 # just empirically, I need to scale up the reflection by a factor of 2 in order to get it to be the right size
    try_again = False
    while try_again:
        data_name = 'capture1'
        d.name(data_name)
        try:
            d.hdf5_write('201020_sol_probe_1.h5')
            try_again = False
        except Exception as e:
            print(e)
            print("name taken, trying again...")
            try_again = True
    print(("name of data",d.name()))
    print(("units should be",d.get_units('t')))
    print(("shape of data",ndshape(d)))
    fl.next('waveforms')
    fl.plot(d, alpha=0.1)
    fl.plot(abs(d), alpha=0.5, linewidth=3)
    fl.plot(abs(flat_slice), alpha=0.5, linewidth=3)
flat_slice.run(abs).mean('t')
print("reflection ratio calculated from ratio of %f to %f mV"%(abs(flat_slice['ch',1]).item()/1e-3,abs(flat_slice['ch',0]).item()/1e-3))
ratio = (abs(flat_slice['ch',1]/flat_slice['ch',0])).item()
tuning_dB = log10(ratio)*20
if tuning_dB < -25:
    print("congratulations! you have achieved a reflection ratio of %0.1f dB"%tuning_dB)
else:
    print("Sorry! Your reflection ratio is %0.1f dB.  TRY HARDER!!!!"%tuning_dB)

