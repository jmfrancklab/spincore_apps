from pyspecdata import *
import os
import SpinCore_pp
import socket
import sys
import time
from datetime import datetime
import numpy as np
fl = figlist_var()
#{{{ Verify arguments compatible with board
def verifyParams():
    if (nPoints > 16*1024 or nPoints < 1):
        print("ERROR: MAXIMUM NUMBER OF POINTS IS 16384.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED NUMBER OF POINTS.")
    if (nScans < 1):
        print("ERROR: THERE MUST BE AT LEAST 1 SCAN.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED NUMBER OF SCANS.")
    if (p90 < 0.065):
        print("ERROR: PULSE TIME TOO SMALL.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED PULSE TIME.")
    if (tau < 0.065):
        print("ERROR: DELAY TIME TOO SMALL.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED DELAY TIME.")
    return
#}}}
#{{{ for setting EPR magnet
def API_sender(value):
    IP = "jmfrancklab-bruker.syr.edu"
    if len(sys.argv) > 1:
        IP = sys.argv[1]
    PORT = 6001
    print("target IP:", IP)
    print("target port:", PORT)
    MESSAGE = str(value)
    print("SETTING FIELD TO...", MESSAGE)
    sock = socket.socket(socket.AF_INET, # Internet
            socket.SOCK_STREAM) # TCP
    sock.connect((IP, PORT))
    sock.send(MESSAGE)
    sock.close()
    print("FIELD SET TO...", MESSAGE)
    time.sleep(5)
    return
#}}}
#{{{ Edit here to set the actual field
set_field = False
if set_field:
    B0 = 3497 # Determine this from Field Sweep
    API_sender(B0)
#}}}
date = datetime.now().strftime('%y%m%d')
output_name = 'Ni_sol_probe_nutation_amp_3'
adcOffset = 41
carrierFreq_MHz = 14.891248
tx_phases = r_[0.0,90.0,180.0,270.0]
nScans = 1
nEchoes = 1
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
GDS = True
deadtime = 10.0
repetition = 1.3e6
SW_kHz = 50.0
aq = 24564
nPoints = 2048#int(aq/SW_kHz+0.5)#1024*2
acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
tau = 5e3#deadtime + acq_time*1e3*(1./8.) + tau_adjust
p90 = 250#us (28x expected 90 time)
print("ACQUISITION TIME:",acq_time,"ms")
print("TAU DELAY:",tau,"us")
data_length = 2*nPoints*nEchoes*nPhaseSteps
amp_range = np.linspace(0,0.5,200)[1:]#,endpoint=False)
datalist = []
#{{{ setting acq_params dictizaonary
acq_params = {}
acq_params['adcOffset'] = adcOffset
acq_params['carrierFreq_MHz'] = carrierFreq_MHz
acq_params['amplitude'] = amp_range
acq_params['nScans'] = nScans
acq_params['nEchoes'] = nEchoes
acq_params['p90_us'] = p90
acq_params['deadtime_us'] = deadtime
acq_params['repetition_us'] = repetition
acq_params['SW_kHz'] = SW_kHz
acq_params['nPoints'] = nPoints
acq_params['tau_adjust_us'] = tau_adjust
acq_params['deblank_us'] = 1.0
acq_params['tau_us'] = tau
#acq_params['pad_us'] = pad 
#}}}
with GDS_scope as g:
    g.acquire_mode('HIR')
#set impedance to 50 ohms
#set timescale, volts
    for index,val in enumerate(amp_range):
        #p90 = val # us
        amplitude = val # pulse amp, set from 0.0 to 1.0
        print("***")
        print("INDEX %d - AMPLITUDE %f"%(index,val))
        print("***")
        SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
        acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
        acq_params['acq_time_ms'] = acq_time
        SpinCore_pp.init_ppg();
        spincore_pp.load([
            ('marker','start',nScans),
            ('phase_reset',1),
            ('delay_ttl',1.0),
            ('pulse_ttl',p90,0.0),
            ('delay',tau),
            ('delay_ttl',1.0),
            ('pulse_ttl',2.0*p90,0.0),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',repetition),
            ('jumpto','start')
            ])
        spincore_pp.stop_ppg();
        spincore_pp.runboard();
        #might need delay
        datalist.append(g.waveform(ch=1))
        # according to jf, this commented out line
        # should work same as line below and be more effic
        SpinCore_pp.stopBoard();
nutation_data = concat(datalist,'amplitudes').reorder('t')

j = 1
try_again = True
print("writing to file now")
while try_again:
    data_name = 'capture%d'%j
    data.name(data_name)
    try:
        data.hdf5_write('201229_notunelimiter_7.h5')
        try_again = False
    except Exception as e:
        print(e)
        print("name taken, trying again...")
        j += 1
        try_again = True
print(("name of data",data.name()))
print(("units should be",data.get_units('t')))
fl.next('Dual-channel data')
fl.plot(data)

