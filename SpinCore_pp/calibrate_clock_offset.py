#To use, copy vd_list from an inversion recovery experiment,
#and hook up TX into scope and make sure RX is covered with 50 ohm resistor
#then run this program. The final data point will be the time-dependent
#phase error of the board which can then be used to correct the signal acquired
#in the inversion recovery experiment.

from pyspecdata import *
import os
import SpinCore_pp
import socket
import sys
import time
init_logging(level='debug')
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
date = '190417'
#clock_correction = -10.51/6 # clock correction in radians per second (additional phase accumulated after phase_reset)
#clock_correction = -3.8/1.6
#clock_correction = -0.05/10. + -3.55793/998.7
clock_correction = 0
#clock_correction = 1.20097294/10. - 7.09889739/10.
output_name = 'calibrate_clock'
adcOffset = 41
carrierFreq_MHz = 14.86 
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
# all times are in us
# except acq_time in ms
p90 = 4.0
tau_adjust = 0.0
transient = 100.0
repetition = 1e6
#SW_kHz = 80.0
#nPoints = 128
SW_kHz = 15.0
nPoints = 256
nScans = 1
nEchoes = 1
nPhaseSteps = 1 
data_length = 2*nPoints*nEchoes*nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
#vd_list = r_[1e1,1e2,1e3,1e4,1e5,1e6,5e6]
vd_list = r_[9.5e1,5e3,6.5e4,8e4,9.2e4,1e5,1.7e5,1e6,3e6,5e6]
#vd_list = r_[1e3,
#        1e6,
#        6e6,
#        9e6]
#vd_list = r_[1e3,3e3,5e3]
for index,val in enumerate(vd_list):
    vd = val
    print "***"
    print "INDEX %d - VARIABLE DELAY %f"%(index,val)
    print "***"
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    tau = (acq_time*1000.0+transient+tau_adjust)/2.0
    SpinCore_pp.init_ppg();
    SpinCore_pp.load([
        ('marker','start',nScans),
        ('phase_reset',1),
        ('delay',vd),
        ('pulse',p90,0.0),
        ('delay',tau),
        ('pulse',2.0*p90,0.0),
        ('delay',transient),
        ('acquire',acq_time),
        ('delay',repetition),
        ('jumpto','start')
        ])
    SpinCore_pp.stop_ppg();
    print "\nRUNNING BOARD...\n"
    start = time.time()
    SpinCore_pp.runBoard(); 
    runtime = time.time()-start
    logger.debug(strm("for vd",vd/1e6," s run time is",runtime))
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
        vd_data = ndshape([len(vd_list),len(time_axis)],['vd','t']).alloc(dtype=complex128)
        vd_data.setaxis('vd',vd_list*1e-6).set_units('vd','s')
        vd_data.setaxis('t',time_axis).set_units('t','s')
    vd_data['vd',index] = data
SpinCore_pp.stopBoard();
print "EXITING...\n"
print "\n*** *** ***\n"
save_file = True
while save_file:
    try:
        print "SAVING FILE..."
        vd_data.name('signal')
        vd_data.hdf5_write(date+'_'+output_name+'.h5')
        print "Name of saved data",vd_data.name()
        print "Units of saved data",vd_data.get_units('t')
        print "Shape of saved data",ndshape(vd_data)
        save_file = False
    except Exception as e:
        print e
        print "FILE ALREADY EXISTS."
        save_file = False
fl.next('raw data')
vd_data *= exp(-1j*vd_data.fromaxis('vd')*clock_correction)
manual_taxis_zero = acq_time*1e-3/2.0 #2.29e-3
vd_data.setaxis('t',lambda x: x-manual_taxis_zero)
fl.image(vd_data)
vd_data.ft('t',shift=True)
fl.next('FT raw data')
fl.image(vd_data)
fl.next('phase error vs. vd')
fl.plot(vd_data.sum('t').angle,'o')
fl.next('phase error, unwrapped vs. vd')
vd_data = vd_data['vd',1:]/vd_data['vd',:-1]
vd_data = vd_data.angle.name('signal phase').set_units('rad')
vd_data.data = vd_data.data.cumsum()
fl.plot(vd_data,'o')
fl.show()
print vd_data

