#{{{ Program doc
r'''Use this program to determine the time-dependent phase error of the SpinCore
board, specifically between the transmit clock (which gives the phase of the rf
pulses) and the receiver clock (which mixes down the signal to give the acquired
data).

Remember that a linear time-dependent phase is a frequency -- here we have a frequency difference
:math:`\Delta \nu` between :math:`\nu_{tx}` and :math:`\nu_{tx}` (:math:`\Delta
\nu=\nu_{rx}-\nu_{tx}` that gives rise to a phase that looks like this:
:math:`\exp(i 2 \pi \Delta \nu t)` -- note how this is a phase that varies linearly with :math:`t`.
The phase reset command sets the phase of both Tx and Rx, so :math:`t` here is
the time since the last phase reset.

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
from datetime import datetime
#init_logging(level='debug')
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
date = datetime.now().strftime('%y%m%d')
clock_correction = 0
output_name = 'calibrate_clock_3'
adcOffset = 41
carrierFreq_MHz = 14.896933
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 16
nEchoes = 1
nPhaseSteps = 1 
p90 = 3.8
deadtime = 5.0
repetition = 10e6
deblank = 1.0
SW_kHz = 24.0
nPoints = 1024*2
acq_time = nPoints/SW_kHz
tau_adjust = 0.0
tau = deadtime + acq_time*1e3*0.5 + tau_adjust
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
#}}}
print("ACQUISITION TIME:",acq_time,"ms")
print("TAU DELAY:",tau,"us")
# NOTE: Number of segments is nEchoes * nPhaseSteps
vd_list = r_[5e1,6.67e5,1.3e6,2e6,2.67e6,3.33e6,4e6,4.67e6,5.33e6,6e6,6.67e6,7.33e6,8e6,8.67e6,9.33e6,10e6]

for scan_num in range(nScans):
    for index,val in enumerate(vd_list):
        vd = val
        print("***")
        print("INDEX %d - VARIABLE DELAY %f"%(index,val))
        print("***")
        SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
        acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
        SpinCore_pp.init_ppg();
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay',vd),
            ('delay_TTL',deblank),
            ('pulse_TTL',p90,0),
            ('delay',tau),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,0),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',repetition),
            ('jumpto','start')
            ])
        SpinCore_pp.stop_ppg();
        print("\nRUNNING BOARD...\n")
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
        print("COMPLEX DATA ARRAY LENGTH:",shape(data)[0])
        print("RAW DATA ARRAY LENGTH:",shape(raw_data)[0])
        dataPoints = float(shape(data)[0])
        time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
        data = nddata(array(data),'t')
        data.setaxis('t',time_axis).set_units('t','s')
        data.name('signal')
        if index == 0 and scan_num == 0:
            vd_data = ndshape([nScans,len(vd_list),len(time_axis)],['nScans','vd','t']).alloc(dtype=complex128)
            vd_data.setaxis('nScans',r_[0:nScans])
            vd_data.setaxis('vd',vd_list*1e-6).set_units('vd','s')
            vd_data.setaxis('t',time_axis).set_units('t','s')
            vd_data.set_prop('acq_params',acq_params)
        vd_data['vd',index]['nScans',scan_num] = data
SpinCore_pp.stopBoard();
print("EXITING...\n")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        print("SAVING FILE...")
        vd_data.name('signal')
        vd_data.hdf5_write(date+'_'+output_name+'.h5')
        print("Name of saved data",vd_data.name())
        print("Units of saved data",vd_data.get_units('t'))
        print("Shape of saved data",ndshape(vd_data))
        save_file = False
    except Exception as e:
        print(e)
        print("FILE ALREADY EXISTS.")
        save_file = False
fl.next('raw data')
vd_data *= exp(-1j*vd_data.fromaxis('vd')*clock_correction)
manual_taxis_zero = acq_time*1e-3/2.0 #2.29e-3
vd_data.setaxis('t',lambda x: x-manual_taxis_zero)
fl.image(vd_data)
vd_data.ft('t',shift=True)
fl.next('FT raw data')
fl.image(vd_data)
fl.show()

