from pyspecdata import *
import os
from . import SpinCore_pp
import socket
import sys
import time
fl = figlist_var()
#{{{ Verify arguments compatible with board
def verifyParams():
    if (nPoints > 16*1024 or nPoints < 1):
        print("ERROR: MAXIMUM NUMBER OF POINTS IS 16384.")
        print("EXITING.")
        raise RuntimeError("Someone included a quit statement here.  This is evil!! FIX!!!")
    else:
        print("VERIFIED NUMBER OF POINTS.")
    if (nScans < 1):
        print("ERROR: THERE MUST BE AT LEAST 1 SCAN.")
        print("EXITING.")
        raise RuntimeError("Someone included a quit statement here.  This is evil!! FIX!!!")
    else:
        print("VERIFIED NUMBER OF SCANS.")
    if (p90 < 0.065):
        print("ERROR: PULSE TIME TOO SMALL.")
        print("EXITING.")
        raise RuntimeError("Someone included a quit statement here.  This is evil!! FIX!!!")
    else:
        print("VERIFIED PULSE TIME.")
    if (tau < 0.065):
        print("ERROR: DELAY TIME TOO SMALL.")
        print("EXITING.")
        raise RuntimeError("Someone included a quit statement here.  This is evil!! FIX!!!")
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
set_field = False
if set_field:
    B0 = 3409.3 # Determine this from Field Sweep
    API_sender(B0)
date = '190201'
output_name = 'MWE_GDS'
adcOffset = 49
carrierFreq_MHz = 14.46
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
nPhaseSteps = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
RX_delay = 120.0
repetition = 2.0e6
SW_kHz = 20.0
nPoints = 64
acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
tau = RX_delay + acq_time*1e3*0.5 + tau_adjust
print("ACQUISITION TIME:",acq_time,"ms")
print("TAU DELAY:",tau,"us")
data_length = 2*nPoints*nEchoes*nPhaseSteps
p90 = 10.44
num_transients = 100
for index in range(num_transients):
    transient = index+1
    print("***")
    print("TRANSIENT NUMBER: %d"%(transient))
    print("***")
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    SpinCore_pp.init_ppg();
    SpinCore_pp.load([
        ('marker','start',nScans),
        ('phase_reset',1),
        ('pulse',p90,0.0),
        ('delay',tau),
        ('pulse',2.0*p90,0.0),
        ('delay',RX_delay),
        ('acquire',acq_time),
        ('delay',repetition),
        ('jumpto','start')
        ])
    SpinCore_pp.stop_ppg();
    SpinCore_pp.runBoard();
    raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
    raw_data.astype(float)
    data = []
    # according to JF, this commented out line
    # should work same as line below and be more effic
    #data = raw_data.view(complex128)
    data[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
    print("COMPLEX DATA ARRAY LENGTH:",shape(data)[0])
    print("RAW DATA ARRAY LENGTH:",shape(raw_data)[0])
    dataPoints = float(shape(data)[0])
    time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
    data = nddata(array(data),'t')
    data.setaxis('t',time_axis).set_units('t','s')
    data.name('signal')
    if index == 0:
        transient_data = ndshape([num_transients,len(time_axis)],['trans_no','t']).alloc(dtype=complex128)
        transient_data.setaxis('trans_no',transient)
        transient_data.setaxis('t',time_axis).set_units('t','s')
    transient_data['trans_no',index] = data
SpinCore_pp.stopBoard();
print("EXITING...\n")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        print("SAVING FILE...")
        transient_data.name('transients')
        transient_data.hdf5_write(date+'_'+output_name+'.h5')
        print("Name of saved data",transient_data.name())
        print("Units of saved data",transient_data.get_units('t'))
        print("Shape of saved data",ndshape(transient_data))
        save_file = False
    except Exception as e:
        print(e)
        print("FILE ALREADY EXISTS.")
        save_file = False
fl.next('raw data')
fl.image(transient_data)
transient_data.ft('t',shift=True)
fl.next('FT raw data')
fl.image(transient_data)
fl.show()

