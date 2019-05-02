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
import SpinCore_pp 
import time
fl = figlist_var()

date = '190423'
output_name = 'T1CPMG_1'
#clock_correction = -10.51/6 # clock correction in radians per second (additional phase accumulated after phase_reset)
#clock_correction = 4.27/10.
clock_correction = 0
adcOffset = 42
carrierFreq_MHz = 14.860135
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
p90 = 3.75
deadtime = 50.0
repetition = 4e6

SW_kHz = 15.0
nPoints = 128

deblank = 1.0
acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
tau = deadtime + acq_time*1e3*0.5 + tau_adjust
pad = 2.0*tau - deadtime - acq_time*1e3 - 2.0*p90 - deblank
print "ACQUISITION TIME:",acq_time,"ms"
print "TAU DELAY:",tau,"us"
print "PAD DELAY:",pad,"us"
nScans = 4
nEchoes = 64
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 2
if not phase_cycling:
    nPhaseSteps = 1 
data_length = 2*nPoints*nEchoes*nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
vd_list = r_[1e0,1e1,1e2,5e3,5e4,7.5e4,8.5e4,9e4,9.5e4,9.6e4,9.7e4,9.8e4,9.9e4,1e5,3e5,7e5,1e6]
for index,val in enumerate(vd_list):
    vd = val
    print "***"
    print "INDEX %d - VARIABLE DELAY %f"%(index,val)
    print "***"
    SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
    acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
    SpinCore_pp.init_ppg();
    if phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('delay_TTL',deblank),
            ('pulse_TTL',2.0*p90,0.0),
            ('delay',vd),
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
            ('pulse_TTL',2.0*p90,0.0),
            ('delay',vd),
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
        data_2d = ndshape([len(vd_list),len(time_axis)],['vd','t']).alloc(dtype=complex128)
        data_2d.setaxis('vd',vd_list*1e-6).set_units('vd','s')
        data_2d.setaxis('t',time_axis).set_units('t','s')
    data_2d['vd',index] = data
SpinCore_pp.stopBoard();
print "EXITING..."
print "\n*** *** ***\n"
save_file = True
while save_file:
    try:
        print "SAVING FILE..."
        data_2d.name('signal')
        data_2d.hdf5_write(date+'_'+output_name+'.h5')
        print "Name of saved data",data_2d.name()
        print "Units of saved data",data_2d.get_units('t')
        print "Shape of saved data",ndshape(data_2d)
        save_file = False
    except Exception as e:
        print e
        print "FILE ALREADY EXISTS."
        save_file = False
fl.next('raw data')
data_2d *= exp(-1j*data_2d.fromaxis('vd')*clock_correction)
manual_taxis_zero = acq_time*1e-3/2.0 #2.29e-3
data_2d.setaxis('t',lambda x: x-manual_taxis_zero)
fl.image(data_2d)
data_2d.ft('t',shift=True)
fl.next('FT raw data')
fl.image(data_2d)
fl.show()

