from pyspecdata import *
import os
import SpinCore_pp
import socket
import sys
import time
fl = figlist_var()
#{{{ Verify arguments compatible with board
def verifyParams():
    if (nPoints > 16*1024 or nPoints < 1):
        print "ERROR: MAXIMUM NUMBER OF POINTS IS 16384."
        print "EXITING."
        quit()
    else:
        print "VERIFIED NUMBER OF POINTS."
    if (nScans < 1):
        print "ERROR: THERE MUST BE AT LEAST 1 SCAN."
        print "EXITING."
        quit()
    else:
        print "VERIFIED NUMBER OF SCANS."
    if (p90 < 0.065):
        print "ERROR: PULSE TIME TOO SMALL."
        print "EXITING."
        quit()
    else:
        print "VERIFIED PULSE TIME."
    if (tau < 0.065):
        print "ERROR: DELAY TIME TOO SMALL."
        print "EXITING."
        quit()
    else:
        print "VERIFIED DELAY TIME."
    return
#}}}
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
    time.sleep(20)
    return
set_field = False
if set_field:
    B0 = 3409.3 # Determine this from Field Sweep
    API_sender(B0)
date = '190103'
output_name = 'nutation_3'
adcOffset = 46
carrierFreq_MHz = 14.46
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
SW_kHz = 25.0
nPoints = 128
nScans = 10 
nEchoes = 1
nPhaseSteps = 1
tau_adjust = 440.0
transient = 500.0
repetition = 1e6
data_length = 2*nPoints*nEchoes*nPhaseSteps
p90_range = linspace(0.1,4.5,44,endpoint=False)
for index,val in enumerate(p90_range):
    p90 = val # us
    print "***"
    print "INDEX %d - 90 TIME %f"%(index,val)
    print "***"
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    tau = (acq_time*1000.0+transient+tau_adjust)/2.0
    SpinCore_pp.init_ppg();
    SpinCore_pp.load([
        ('marker','start',nScans),
        ('phase_reset',1),
        ('pulse',p90,0.0),
        ('delay',tau),
        ('pulse',2.0*p90,0.0),
        ('delay',transient),
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
    print "COMPLEX DATA ARRAY LENGTH:",shape(data)[0]
    print "RAW DATA ARRAY LENGTH:",shape(raw_data)[0]
    dataPoints = float(shape(data)[0])
    time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
    data = nddata(array(data),'t')
    data.setaxis('t',time_axis).set_units('t','s')
    data.name('signal')
    if index == 0:
        nutation_data = ndshape([len(p90_range),len(time_axis)],['p_90','t']).alloc(dtype=complex128)
        nutation_data.setaxis('p_90',p90_range*1e-6).set_units('p_90','s')
        nutation_data.setaxis('t',time_axis).set_units('t','s')
    nutation_data['p_90',index] = data
SpinCore_pp.stopBoard();
print "EXITING...\n"
print "\n*** *** ***\n"
save_file = True
while save_file:
    try:
        print "SAVING FILE..."
        nutation_data.name('nutation')
        nutation_data.hdf5_write(date+'_'+output_name+'.h5')
        print "Name of saved data",nutation_data.name()
        print "Units of saved data",nutation_data.get_units('t')
        print "Shape of saved data",ndshape(nutation_data)
        save_file = False
    except Exception as e:
        print e
        print "FILE ALREADY EXISTS."
        save_file = False
fl.next('raw data')
fl.image(nutation_data)
nutation_data.ft('t',shift=True)
fl.next('FT raw data')
fl.image(nutation_data)
fl.show()

