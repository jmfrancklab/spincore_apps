#{{{ Program doc
r'''Use this program to determine the time-dependent phase error of the SpinCore
board, specifically between the transmit clock (which gives the phase of the rf
pulses) and the receiver clock (which mixes down the signal to give the acquired
data).

This program requires the spectrometer to be fully up and
running, ready for signal acquisition (i.e., magnet on, amplifiers on).

It collects data for a pulse sequence that consists of a phase reset - variable
delay - spin echo.

For best results, the variable delay list should match that
of an inversion recovery or other similar experiment. It is for these types of experiments,
during which long delays occur within the pulse sequence itself, that this phase drift can occur.
'''
#}}}
from pyspecdata import *
import os
import SpinCore_pp
import socket
import sys
import time
#init_logging(level='debug')
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
date = '190614'
#clock_correction = -10.51/6 # clock correction in radians per second (additional phase accumulated after phase_reset)
clock_correction = 0
output_name = 'calibrate_clock_1'
adcOffset = 35
carrierFreq_MHz = 14.894351
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
nPhaseSteps = 1 
p90 = 3.2
deadtime = 100.0
repetition = 4e6
deblank = 1.0
SW_kHz = 15.0
nPoints = 128
acq_time = nPoints/SW_kHz
tau_adjust = 0.0
tau = deadtime + acq_time*1e3*0.5 + tau_adjust
data_length = 2*nPoints*nEchoes*nPhaseSteps
print "ACQUISITION TIME:",acq_time,"ms"
print "TAU DELAY:",tau,"us"
# NOTE: Number of segments is nEchoes * nPhaseSteps
vd_list = r_[1e1,1e2,1e3,1e4,1e5,1e6,1e7]
for index,val in enumerate(vd_list):
    vd = val
    print "***"
    print "INDEX %d - VARIABLE DELAY %f"%(index,val)
    print "***"
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    SpinCore_pp.init_ppg();
    SpinCore_pp.load([
        ('marker','start',nScans),
        ('phase_reset',1),
        ('delay',vd),
        ('delay_TTL',deblank),
        ('pulse_TTL',p90,0.0),
        ('delay',tau),
        ('delay_TTL',deblank),
        ('pulse_TTL',2.0*p90,0.0),
        ('delay',deadtime),
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

