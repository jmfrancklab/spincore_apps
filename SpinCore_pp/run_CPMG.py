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
date = '190201'
output_name = 'CPMG_v3'
adcOffset = 49
carrierFreq_MHz = 14.46 
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
transient = 120.0
repetition = 1e6
SW_kHz = 20.0
nPoints = 64
acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
nScans = 1
nEchoes = 64
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1 
data_length = 2*nPoints*nEchoes*nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
p90_range = linspace(0.869,0.889,20,endpoint=False)
for index,p90 in enumerate(p90_range):
    tau = transient + acq_time*1e3*0.5 + tau_adjust
    pad = 2.0*tau - transient - acq_time*1e3 - 2.0*p90
    print "ACQUISITION TIME:",acq_time,"ms"
    print "TAU DELAY:",tau,"us"
    print "PAD DELAY:",pad,"us"
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
    print "\nINITIALIZING PROG BOARD...\n"
    SpinCore_pp.init_ppg();
    print "\nLOADING PULSE PROG...\n"
    if phase_cycling:
        SpinCore_pp.load([
            ('marker','start',1),
            ('phase_reset',1),
            ('pulse',p90,'ph1',r_[0,1,2,3]),
            ('delay',tau),
            ('pulse',2.0*p90,0.0),
            ('delay',transient),
            ('acquire',acq_time),
            ('delay',pad),
            ('marker','echo_label',(nEchoes-1)),
            ('pulse',2.0*p90,0.0),
            ('delay',transient),
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
            ('pulse',p90,0.0),
            ('delay',tau),
            ('pulse',2.0*p90,0.0),
            ('delay',transient),
            ('acquire',acq_time),
            ('delay',pad),
            ('marker','echo_label',(nEchoes-1)),
            ('pulse',2.0*p90,0.0),
            ('delay',transient),
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
    if index == 0:
        CPMG_data = ndshape([len(p90_range),len(time_axis)],['p_90','t']).alloc(dtype=complex128)
        CPMG_data.setaxis('p_90',p90_range*1e-6).set_units('p_90','s')
        CPMG_data.setaxis('t',time_axis).set_units('t','s')
    CPMG_data['p_90',index] = data
SpinCore_pp.stopBoard();
print "EXITING..."
print "\n*** *** ***\n"
save_file = True
while save_file:
    try:
        print "SAVING FILE..."
        CPMG_data.name('CPMG_data')
        CPMG_data.hdf5_write(date+'_'+output_name+'.h5')
        print "Name of saved data",CPMG_data.name()
        print "Units of saved data",CPMG_data.get_units('t')
        print "Shape of saved data",ndshape(CPMG_data)
        save_file = False
    except Exception as e:
        print e
        print "FILE ALREADY EXISTS."
        save_file = False
fl.next('raw data')
fl.image(CPMG_data)
CPMG_data.ft('t',shift=True)
fl.next('FT raw data')
fl.image(CPMG_data)
fl.show()
