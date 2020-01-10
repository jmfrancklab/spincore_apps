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
fl = figlist_var()

date = '200108'
output_name = 'CPMG_calib_1'
adcOffset = 48
carrierFreq_MHz = 14.898939
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
deadtime = 60.0
repetition = 15e6

SW_kHz = 4.0
nPoints = 128

deblank = 1.0
acq_time = nPoints/SW_kHz # ms
tau_adjust = 1000.
tau = deadtime + acq_time*1e3*0.5 + tau_adjust
nScans = 1
nEchoes = 64
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 2
if not phase_cycling:
    nPhaseSteps = 1 
data_length = 2*nPoints*nEchoes*nPhaseSteps
p90_range = linspace(3.0,9.0,3)#,endpoint=False)
#{{{ setting acq_params dictionary
acq_params = {}
acq_params['adcOffset'] = adcOffset
acq_params['carrierFreq_MHz'] = carrierFreq_MHz
acq_params['amplitude'] = amplitude
acq_params['nScans'] = nScans
acq_params['nEchoes'] = nEchoes
acq_params['p90_us'] = p90_range
acq_params['deadtime_us'] = deadtime
acq_params['repetition_us'] = repetition
acq_params['SW_kHz'] = SW_kHz
acq_params['nPoints'] = nPoints
acq_params['tau_adjust_us'] = tau_adjust
acq_params['deblank_us'] = deblank
acq_params['tau_us'] = tau
if phase_cycling:
    acq_params['nPhaseSteps'] = nPhaseSteps
#}}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
for index,val in enumerate(p90_range):
    p90 = val # us
    pad = 2.0*tau - deadtime - acq_time*1e3 - 2.0*p90 - deblank
    print "ACQUISITION TIME:",acq_time,"ms"
    print "TAU DELAY:",tau,"us"
    print "PAD DELAY:",pad,"us"
    print "***"
    print "INDEX %d - 90 TIME %f"%(index,val)
    print "***"
    for x in xrange(nScans):
        SpinCore_pp.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
        acq_time = SpinCore_pp.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
        acq_params['acq_time_ms'] = acq_time
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
        SpinCore_pp.stop_ppg();
        SpinCore_pp.runBoard();
        raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
        raw_data.astype(float)
        data = []
        data[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
        print "COMPLEX DATA ARRAY LENGTH:",shape(data)[0]
        print "RAW DATA ARRAY LENGTH:",shape(raw_data)[0]
        dataPoints = float(shape(data)[0])
        if x == 0:
            if index == 0:
                print " *** *** ***"
                print "INITILIAZING NDDATA..."
                print " *** *** ***"
                time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
                nutation_data = ndshape([len(p90_range),len(time_axis),nScans],['p_90','t','nScans']).alloc(dtype=complex128)
                nutation_data.setaxis('p_90',p90_range*1e-6).set_units('p_90','s')
                nutation_data.setaxis('t',time_axis).set_units('t','s')
                nutation_data.setaxis('nScans',r_[0:nScans])
        nutation_data['p_90',index]['nScans',x] = data
    SpinCore_pp.stopBoard();
print "EXITING..."
print "\n*** *** ***\n"
save_file = True
while save_file:
    try:
        print "SAVING FILE..."
        nutation_data.set_prop('acq_params',acq_params)
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