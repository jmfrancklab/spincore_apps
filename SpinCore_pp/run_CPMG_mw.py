#{{{ note on phase cycling
'''
FOR PHASE CYCLING: Provide both a phase cycle label (e.g.,
'ph1', 'ph2') as str and an array containing the indices
(i.e., registers) of the phases you which to use that are
specified in the numpy array 'tx_phases'.  Note that
specifying the same phase cycle label will loop the
corresponding phase steps together, regardless of whether
the indices are the same or not.
    e.g.,
    The following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph1',r_[2,3]),
    will provide two transients with phases of the two pulses (p1,p2):
        (0,2)
        (1,3)
    whereas the following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph2',r_[2,3]),
    will provide four transients with phases of the two pulses (p1,p2):
        (0,2)
        (0,3)
        (1,2)
        (1,3)
FURTHER: The total number of transients that will be
collected are determined by both nScans (determined when
calling the appropriate marker) and the number of steps
calculated in the phase cycle as shown above.  Thus for
nScans = 1, the SpinCore will trigger 2 times in the first
case and 4 times in the second case.  for nScans = 2, the
SpinCore will trigger 4 times in the first case and 8 times
in the second case.
'''
#}}}
from pyspecdata import *
from numpy import *
import os
import sys
import SpinCore_pp
from Instruments import Bridge12,prologix_connection,gigatronics
from serial import Serial
import time

fl = figlist_var()
# Parameters for Bridge12
powers = r_[1e-3:4.0:10j]
dB_settings = round_(2*log10(powers/1e-3)*10.)/2
dB_settings = unique(dB_settings)
def check_for_3dB_step(x):
    assert len(x.shape) == 1
    if any(diff(x) > 3.0):
        idx = nonzero(diff(x) > 3)[0][0]
        x = insert(x,idx+1,r_[x[idx]:x[idx+1]:3.0][1:])
        x = check_for_3dB_step(x)
        return x
    else:
        return x
ini_len = len(dB_settings)
dB_settings = check_for_3dB_step(dB_settings)
print "adjusted my power list by",len(dB_settings)-len(powers),"to satisfy the 3dB step requirement and the 0.5 dB resolution"
powers = 1e-3*10**(dB_settings/10.)

date = '191121'
output_name = 'CPMG_DNP_1'
adcOffset = 35 
carrierFreq_MHz = 14.898410
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
p90 = 3.3
deadtime = 60.0
repetition = 15e6

SW_kHz = 9.0
nPoints = 128

deblank = 1.0
acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
tau = deadtime + acq_time*1e3*0.5 + tau_adjust
pad = 2.0*tau - deadtime - acq_time*1e3 - 2.0*p90 - deblank
print "ACQUISITION TIME:",acq_time,"ms"
print "TAU DELAY:",tau,"us"
print "PAD DELAY:",pad,"us"
nScans = 1
nEchoes = 64
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 2
if not phase_cycling:
    nPhaseSteps = 1 
data_length = 2*nPoints*nEchoes*nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
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
print "\n*** *** ***\n"
print "CONFIGURING TRANSMITTER..."
SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
print "\nTRANSMITTER CONFIGURED."
print "***"
print "CONFIGURING RECEIVER..."
acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
acq_params['acq_time_ms'] = acq_time
print "\nRECEIVER CONFIGURED."
print "***"
print "\nINITIALIZING PROG BOARD...\n"
SpinCore_pp.init_ppg();
print "\nLOADING PULSE PROG...\n"
if phase_cycling:
    SpinCore_pp.load([
        ('marker','start',1),
        ('phase_reset',1),
            ('delay_TTL',deblank),
            ('pulse_TTL',p90,'ph1',r_[0,2]),
            ('delay',tau),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,1),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',pad),
            ('marker','echo_label',(nEchoes-1)),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,1),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',pad),
            ('jumpto','echo_label'),
            ('delay',repetition),
            ('jumpto','start')
            ])
    if not phase_cycling:
        SpinCore_pp.load([
            ('marker','start',nScans),
            ('phase_reset',1),
            ('delay_TTL',deblank),
            ('pulse_TTL',p90,0.0),
            ('delay',tau),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,0.0),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',pad),
            ('marker','echo_label',(nEchoes-1)),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,0.0),
            ('delay',deadtime),
            ('acquire',acq_time),
            ('delay',pad),
            ('jumpto','echo_label'),
            ('delay',repetition),
            ('jumpto','start')
            ])
print "\nSTOPPING PROG BOARD...\n"
SpinCore_pp.stop_ppg();
print "\nRUNNING BOARD...\n"
if phase_cycling:
    for x in xrange(nScans):
        print "SCAN NO. %d"%(x+1)
        SpinCore_pp.runBoard();
if not phase_cycling:
    SpinCore_pp.runBoard(); 
raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
raw_data.astype(float)
data = []
data[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
print "COMPLEX DATA ARRAY LENGTH:",shape(data)[0]
print "RAW DATA ARRAY LENGTH:",shape(raw_data)[0]
dataPoints = float(shape(data)[0])
time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
data = nddata(array(data),'t')
data.setaxis('t',time_axis).set_units('t','s')
data.name('signal')
# Define nddata to store along the new power dimension
DNP_data = ndshape([len(powers)+1,len(time_axis)],['power','t']).alloc(dtype=complex128)
DNP_data.setaxis('power',r_[0,powers]).set_units('W')
DNP_data.setaxis('t',time_axis).set_units('t','s')
DNP_data['power',0] = data
#raw_input("CONNECT AND TURN ON BRIDGE12...")
with Bridge12() as b:
    b.set_wg(True)
    b.set_rf(True)
    b.set_amp(True)
    this_return = b.lock_on_dip(ini_range=(9.81e9,9.83e9))
    dip_f = this_return[2]
    print "Frequency",dip_f
    b.set_freq(dip_f)
    meter_powers = zeros_like(dB_settings)
    for j,this_power in enumerate(dB_settings):
        print "\n*** *** *** *** ***\n"
        print "SETTING THIS POWER",this_power,"(",powers[j],"W)"
        b.set_power(this_power)
        time.sleep(15)
        with prologix_connection() as p:
            with gigatronics(prologix_instance=p, address=7) as g:
                meter_powers[j] = g.read_power()
                print "POWER READING",meter_powers[j]
        print "\n*** *** *** *** ***\n"
        print "\n*** *** ***\n"
        print "CONFIGURING TRANSMITTER..."
        SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
        print "\nTRANSMITTER CONFIGURED."
        print "***"
        print "CONFIGURING RECEIVER..."
        acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
        # acq_time is in msec!
        print "\nRECEIVER CONFIGURED."
        print "***"
        # MORE CODE GOES HERE
        print "\nINITIALIZING PROG BOARD...\n"
        SpinCore_pp.init_ppg();
        print "\nLOADING PULSE PROG...\n"
        if phase_cycling:
            SpinCore_pp.load([
                ('marker','start',1),
                ('phase_reset',1),
                    ('delay_TTL',deblank),
                    ('pulse_TTL',p90,'ph1',r_[0,2]),
                    ('delay',tau),
                    ('delay_TTL',deblank),
                    ('pulse_TTL',2.0*p90,1),
                    ('delay',deadtime),
                    ('acquire',acq_time),
                    ('delay',pad),
                    ('marker','echo_label',(nEchoes-1)),
                    ('delay_TTL',deblank),
                    ('pulse_TTL',2.0*p90,1),
                    ('delay',deadtime),
                    ('acquire',acq_time),
                    ('delay',pad),
                    ('jumpto','echo_label'),
                    ('delay',repetition),
                    ('jumpto','start')
                    ])
            if not phase_cycling:
                SpinCore_pp.load([
                    ('marker','start',nScans),
                    ('phase_reset',1),
                    ('delay_TTL',deblank),
                    ('pulse_TTL',p90,0.0),
                    ('delay',tau),
                    ('delay_TTL',deblank),
                    ('pulse_TTL',2.0*p90,0.0),
                    ('delay',deadtime),
                    ('acquire',acq_time),
                    ('delay',pad),
                    ('marker','echo_label',(nEchoes-1)),
                    ('delay_TTL',deblank),
                    ('pulse_TTL',2.0*p90,0.0),
                    ('delay',deadtime),
                    ('acquire',acq_time),
                    ('delay',pad),
                    ('jumpto','echo_label'),
                    ('delay',repetition),
                    ('jumpto','start')
                    ])
        print "\nSTOPPING PROG BOARD...\n"
        SpinCore_pp.stop_ppg();
        print "\nRUNNING BOARD...\n"
        if phase_cycling:
            for x in xrange(nScans):
                print "SCAN NO. %d"%(x+1)
                SpinCore_pp.runBoard();
        if not phase_cycling:
            SpinCore_pp.runBoard(); 
        raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
        raw_data.astype(float)
        data = []
        data[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
        print "COMPLEX DATA ARRAY LENGTH:",shape(data)[0]
        print "RAW DATA ARRAY LENGTH:",shape(raw_data)[0]
        dataPoints = float(shape(data)[0])
        time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
        data = nddata(array(data),'t')
        data.setaxis('t',time_axis).set_units('t','s')
        data.name('signal')
        DNP_data['power',j+1] = data
DNP_data.name('signal')
DNP_data.set_prop('meter_powers',meter_powers)
SpinCore_pp.stopBoard();
print "EXITING..."
print "\n*** *** ***\n"
save_file = True
while save_file:
    try:
        print "SAVING FILE..."
        DNP_data.set_prop('acq_params',acq_params)
        DNP_data.name('signal')
        DNP_data.hdf5_write(date+'_'+output_name+'.h5')
        print "Name of saved data",DNP_data.name()
        print "Units of saved data",DNP_data.get_units('t')
        print "Shape of saved data",ndshape(DNP_data)
        save_file = False
    except Exception as e:
        print e
        print "FILE ALREADY EXISTS."
        save_file = False
fl.next('raw data')
fl.image(DNP_data)
fl.next('abs raw data')
fl.image(abs(DNP_data))
data.ft('t',shift=True)
fl.next('raw data - ft')
fl.image(DNP_data)
fl.next('abs raw data - ft')
fl.image(abs(DNP_data))
fl.show()
