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
date = '190709'
#clock_correction = 4.275439/10. # clock correction in radians per second (additional phase accumulated after phase_reset)
#clock_correction = -0.399405/9.969
clock_correction = 1.0829/998.253
output_name = 'IR_4'
adcOffset = 37
carrierFreq_MHz = 14.897316
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
p90 = 3.35
deadtime = 100.0
repetition = 4e6
SW_kHz = 9.0
nPoints = 128
acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
deblank = 1.0
tau = deadtime + acq_time*1e3*0.5 + tau_adjust
print "ACQUISITION TIME:",acq_time,"ms"
print "TAU DELAY:",tau,"us"
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 8 
if not phase_cycling:
    nPhaseSteps = 1 
data_length = 2*nPoints*nEchoes*nPhaseSteps
#{{{ setting acq_params dictionary
acq_params = {}
acq_params['adcOffset'] = adcOffset
acq_params['carrierFreq_MHz'] = carrierFreq_MHz
acq_params['amplitude'] = amplitude
acq_params['nScans'] = nScans
acq_params['nEchoes'] = nEchoes
acq_params['p90_us'] = p90
acq_params['deadtime_us'] = deadtime
acq_params['repetition_us'] = repetition
acq_params['SW_kHz'] = SW_kHz
acq_params['nPoints'] = nPoints
acq_params['tau_adjust_us'] = tau_adjust
acq_params['deblank_us'] = deblank
acq_params['tau_us'] = tau
acq_params['pad_us'] = pad 
if phase_cycling:
    acq_params['nPhaseSteps'] = nPhaseSteps
#}}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
vd_list = r_[1e1,1e2,1e3,1e4,1e5,1e6,1e7]
#vd_list = r_[3e1,1e2,1e3,3e3,5e3,1e4,3e4,6e4,1e5,3e5,3.5e5,4e5,4.5e5,5e5,5.5e5,6e5,6.5e5,7e5,1e6,3e6,3e6,6e6]
#vd_list = r_[7e4,7.5e4,8e4,8.5e4,9e4,9.5e4,9.8e4]
#vd_list = r_[4.55e5,5e5,6e5,7e5,8e5,9e5,1e6]
#vd_list = r_[7e5,7.1e5,7.2e5,7.3e5,7.4e5,7.5e5,7.6e5,7.7e5,7.8e5,7.9e5,8e5]
for index,val in enumerate(vd_list):
    vd = val
    print "***"
    print "INDEX %d - VARIABLE DELAY %f"%(index,val)
    print "***"
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    acq_params['acq_time_ms'] = acq_time
    SpinCore_pp.init_ppg();
    if phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',1.0),
            ('pulse_TTL',2.0*p90,'ph1',r_[0,2]),
            ('delay',vd),
            ('delay_TTL',1.0),
            ('pulse_TTL',p90,'ph2',r_[0,1,2,3]),
            ('delay',tau),
            ('delay_TTL',1.0),
            ('pulse_TTL',2.0*p90,0.0),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',repetition),
            ('jumpto','start')
            ])
    if not phase_cycling:
        SpinCore_pp.load([
            ('marker','start',nScans),
            ('phase_reset',1),
            ('delay_TTL',1.0),
            ('pulse_TTL',2.0*p90,0.0),
            ('delay',vd),
            ('delay_TTL',1.0),
            ('pulse_TTL',p90,0.0),
            ('delay',tau),
            ('delay_TTL',1.0),
            ('pulse_TTL',2.0*p90,0.0),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',repetition),
            ('jumpto','start')
            ])
    SpinCore_pp.stop_ppg();
    print "\nRUNNING BOARD...\n"
    if phase_cycling:
        for x in xrange(nScans):
            print "SCAN NO. %d"%(x+1)
            SpinCore_pp.runBoard();
    if not phase_cycling:
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
    data.set_prop('acq_params',acq_params)
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
fl.next('abs raw data')
fl.image(abs(vd_data))
vd_data.ft('t',shift=True)
fl.next('FT raw data')
fl.image(vd_data)
fl.next('FT abs raw data')
fl.image(abs(vd_data))
fl.show()

