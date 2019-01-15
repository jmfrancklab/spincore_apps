from pyspecdata import *
import os
import sys
import SpinCore_pp
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
date = '190114'
output_name = 'test_echo_3'
adcOffset = 48
carrierFreq_MHz = 14.46
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
nPhaseSteps = 1
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
p90 = 0.77
transient = 10.0
repetition = 1e6
SW_kHz = 20.0
nPoints = 64
acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
tau = transient + acq_time*1e3*0.5 + tau_adjust
pad = 2.0*tau - transient - acq_time*1e3
print "ACQUISITION TIME:",acq_time,"ms"
print "TAU DELAY:",tau,"us"
print "PAD DELAY:",pad,"us"
data_length = 2*nPoints*nEchoes*nPhaseSteps
print "\n*** *** ***\n"
print "CONFIGURING TRANSMITTER..."
SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
print "\nTRANSMITTER CONFIGURED."
print "***"
print "CONFIGURING RECEIVER..."
acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps)
# acq_time is in msec!
print "ACQUISITION TIME IS",acq_time,"ms"
verifyParams()
print "\nRECEIVER CONFIGURED."
print "***"
print "\nINITIALIZING PROG BOARD...\n"
SpinCore_pp.init_ppg();
print "PROGRAMMING BOARD..."
print "\nLOADING PULSE PROG...\n"
SpinCore_pp.load([
    ('marker','start',nScans),
    ('phase_reset',1),
    ('pulse',p90,0.0),
    ('delay',tau),
    ('pulse',2.0*p90,0.0),
    ('delay',transient),
    ('acquire',acq_time),
    ('delay',pad),
    ('delay',repetition),
    ('jumpto','start')
    ])
print "\nSTOPPING PROG BOARD...\n"
SpinCore_pp.stop_ppg();
print "\nRUNNING BOARD...\n"
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
SpinCore_pp.stopBoard();
print "EXITING..."
print "\n*** *** ***\n"
save_file = True
while save_file:
    try:
        print "SAVING FILE..."
        data.hdf5_write(date+'_'+output_name+'.h5')
        print "Name of saved data",data.name()
        print "Units of saved data",data.get_units('t')
        print "Shape of saved data",ndshape(data)
        save_file = False
    except Exception as e:
        print e
        print "FILE ALREADY EXISTS."
        save_file = False
fl.next('raw data')
fl.plot(data.real,alpha=0.8)
fl.plot(data.imag,alpha=0.8)
fl.plot(abs(data),':',alpha=0.8)
data.ft('t',shift=True)
fl.next('FT raw data')
fl.plot(data.real,alpha=0.8)
fl.plot(data.imag,alpha=0.8)
fl.plot(abs(data),':',alpha=0.8)
fl.show()

