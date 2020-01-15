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

date = '200115'
output_name = 'CPMG_13'
adcOffset = 44
carrierFreq_MHz = 14.898132
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
p90 = 3.4
deadtime = 50.0
repetition = 15e6
deblank = 1.0
marker = 1.0

SW_kHz = 4.0
nPoints = 128
acq_time = nPoints/SW_kHz # ms

tau_extra = 75.0 # us, must be more than deadtime and more than deblank
pad_start = tau_extra - deadtime
pad_end = tau_extra - deblank*2 # marker + deblank
twice_tau = deblank + 2*p90 + deadtime + pad_start + acq_time*1e3 + pad_end + marker
tau1 = twice_tau/2.0
#tau1 = 2*p90 - (2*p90)/pi + pad_start + deadtime + 0.5*acq_time*1e3 - deblank - (2*p90)/pi

print "ACQUISITION TIME:",acq_time,"ms"

nScans = 1
nEchoes = 4
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 2
if not phase_cycling:
    nPhaseSteps = 1 
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
acq_params['deblank_us'] = deblank
acq_params['tau_extra_us'] = tau_extra
acq_params['pad_start_us'] = pad_start
acq_params['pad_end_us'] = pad_end
acq_params['marker_us'] = marker
acq_params['tau1_us'] = tau1
acq_params['SW_kHz'] = SW_kHz
acq_params['nPoints'] = nPoints
if phase_cycling:
    acq_params['nPhaseSteps'] = nPhaseSteps
#}}}
data_length = 2*nPoints*nEchoes*nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
for x in xrange(nScans):
    print "*** *** *** SCAN NO. %d *** *** ***"%(x+1)
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
                ('delay',tau1),
                ('delay_TTL',deblank),
                ('pulse_TTL',2.0*p90,1),
                ('delay',deadtime),
                ('delay',pad_start),
                ('acquire',acq_time),
                ('delay',pad_end),
                ('marker','echo_label',(nEchoes-1)), # 1 us delay
                ('delay_TTL',deblank),
                ('pulse_TTL',2.0*p90,1),
                ('delay',deadtime),
                ('delay',pad_start),
                ('acquire',acq_time),
                ('delay',pad_end),
                ('jumpto','echo_label'), # 1 us delay
                ('delay',repetition),
                ('jumpto','start')
                ])
        if not phase_cycling:
            SpinCore_pp.load([
                ('marker','start',nScans),
                ('phase_reset',1),
                ('delay_TTL',deblank),
                ('pulse_TTL',p90,0.0),
                ('delay',tau1),
                ('delay_TTL',deblank),
                ('pulse_TTL',2.0*p90,0.0),
                ('delay',deadtime),
                ('delay',pad_start),
                ('acquire',acq_time),
                ('delay',pad_end),
                ('marker','echo_label',(nEchoes-1)), # 1 us delay
                ('delay_TTL',deblank),
                ('pulse_TTL',2.0*p90,0.0),
                ('delay',deadtime),
                ('delay',pad_start),
                ('acquire',acq_time),
                ('delay',pad_end),
                ('jumpto','echo_label'), # 1 us delay
                ('delay',repetition),
                ('jumpto','start')
                ])
    print "\nSTOPPING PROG BOARD...\n"
    SpinCore_pp.stop_ppg();
    print "\nRUNNING BOARD...\n"
    SpinCore_pp.runBoard();
    raw_data = SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
    raw_data.astype(float)
    data_array = []
    data_array[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
    print "COMPLEX DATA ARRAY LENGTH:",shape(data_array)[0]
    print "RAW DATA ARRAY LENGTH:",shape(raw_data)[0]
    dataPoints = float(shape(data_array)[0])
    if x == 0:
        time_axis = linspace(0.0,nEchoes*nPhaseSteps*acq_time*1e-3,dataPoints)
        data = ndshape([len(data_array),nScans],['t','nScans']).alloc(dtype=complex128)
        data.setaxis('t',time_axis).set_units('t','s')
        data.setaxis('nScans',r_[0:nScans])
        data.name('signal')
        data.set_prop('acq_params',acq_params)
    data['nScans',x] = data_array
    SpinCore_pp.stopBoard();
print "EXITING..."
print "\n*** *** ***\n"
save_file = True
while save_file:
    try:
        print "SAVING FILE..."
        data.hdf5_write(date+'_'+output_name+'.h5')
        print "FILE SAVED!"
        print "Name of saved data",data.name()
        print "Units of saved data",data.get_units('t')
        print "Shape of saved data",ndshape(data)
        save_file = False
    except Exception as e:
        print e
        print "EXCEPTION ERROR - FILE MAY ALREADY EXIST."
        save_file = False
if not phase_cycling:
    if nScans == 1:
        print ndshape(data)
        fl.next('raw data')
        fl.plot(data)
        fl.plot(abs(data),':',alpha=0.5)
        data.ft('t',shift=True)
        fl.next('raw data - FT')
        fl.plot(data)
        fl.plot(abs(data),':',alpha=0.5)
    else:
        print ndshape(data)
        data.reorder('nScans',first=True)
        fl.next('raw data')
        fl.image(data)
        for x in xrange(len(data.getaxis('nScans'))):
            fl.next('scan %d'%x)
            fl.plot(data['nScans',x])
        data.ft('t',shift=True)
        for x in xrange(len(data.getaxis('nScans'))):
            fl.next('FT scan %d'%x)
            fl.plot(data['nScans',x])
        fl.next('FT raw data')
        fl.image(data)
if phase_cycling:
    print ndshape(data)
    s = data.C
    s.set_units('t','s')
    orig_t = s.getaxis('t')
    acq_time_s = orig_t[nPoints]
    fl.next('time')
    fl.plot(abs(s))
    fl.plot(s.real,alpha=0.4)
    fl.plot(s.imag,alpha=0.4)
    s.ft('t',shift=True)
    fl.next('freq')
    fl.plot(abs(s))
    fl.plot(s.real,alpha=0.4)
    fl.plot(s.imag,alpha=0.4)
fl.show();quit()

