from pylab import *
from Instruments import *
from pyspecdata import *
import os
import sys
import time
import serial
from scipy import signal
import SpinCore_pp
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
        print("VERIFIED DELAY TIME.")
    return
#}}}
def API_sender(value):
    IP = "jmfrancklab-bruker.syr.edu"
    if len(sys.argv)>1:
        IP = sys.argv[1]
    PORT = 6001
    print("target IP:", IP)
    print("target port:",PORT)
    MESSAGE= str(value)
    print("SETTING FIELD TO...",MESSAGE)
    sock = socket.socket(socket.AF_INET,
            socket.SOCK_STREAM)
    sock.connect((IP, PORT))
    sock.send(MESSAGE)
    sock.close()
    print("FIELD SET TO...",MESSAGE)
    time.sleep(5)
    return
date = datetime.now().strftime('%y%m%d')
output_name = 'sol_probe_2'
adcOffset = 42
carrierFreq_MHz = 14.895922
tx_phases = r_[0.0,90.0,180.0,270.0]
nScans = 1
nEchoes = 1
nPhaseSteps = 1
p90 = 9.5
deadtime = 10.0
repetition = 1.3e6
SW_kHz = 100
nPoints = 1024*2
acq_time = nPoints/SW_kHz # ms
deblank = 1.0
tau = 9.5
amp_range = np.linspace(0,0.3,3)

#{{{ setting acq_params dictionary
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
acq_params['deblank_us'] = deblank
#}}}
print(("ACQUISITION TIME:",acq_time,"ms"))
data_length = 2*nPoints*nEchoes*nPhaseSteps
datalist = []
with GDS_scope() as g:
    g.acquire_mode('HIR')

    for index,val in enumerate(amp_range):
        amplitude = val
        print("*** *** ***")
        print("INDEX %d - AMPLITUDE %f"%(index,val))
        print("*** *** ***")
        SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
        acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, 1, nEchoes, nPhaseSteps)
        acq_params['acq_time_ms'] = acq_time
        SpinCore_pp.init_ppg();
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',deblank),
            ('pulse_TTL',p90,0),
            ('delay',tau),
            ('delay',deadtime),
            ('pulse_TTL',2.0*p90,0),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',repetition),
            ('jumpto','start')
            ])
    SpinCore_pp.stop_ppg();
    time.sleep(5)
    SpinCore_pp.runBoard();
    time.sleep(5)
    datalist.append(g.waveform(ch=1))
    SpinCore_pp.stopBoard();
data = concat(datalist,'amplitudes').reorder('t')
j = 1
try_again=True
while try_again:
    data_name = 'capture%d'%j
    data.name(data_name)
    try:
        data.hdf5_write('210201_gds_amp_vary.h5')
        try_again=False
    except Exception as e:
        print(e)
        print("name taken,trying again...")
        j += 1
        try_again=True
print(("units should be",data.get_units('t')))
fl.next('raw data')
fl.plot(data)
fl.show()

