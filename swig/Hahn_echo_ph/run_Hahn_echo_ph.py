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
import Hahn_echo_ph
fl = figlist_var()
date = '181217'
output_name = 'test_Hahn_echo'
adcOffset = 46
carrierFreq_MHz = 14.46 
tx_phases = r_[0.0,90.0,180.0,270.0]
nPhases = 4 
amplitude = 1.0
SW_kHz = 25.0
nPoints = 128
nScans = 4
#{{{ # bit of a hack here to accomplish what JF suggested
     # where I set nEchoes = nScans here
     # which is to acquire several scans in separate 'buffers'
     # or segments, and nEchoes is used (in addition to nPhases)
     # to set the number of segments...
nEchoes = nScans
#}}}
nPhaseSteps = 8 # should come up with way to determine this offhand
                # or rather, from the phase programs that we want to send
                # to the SpinCore
# NOTE: Number of segments is nEchoes * nPhaseSteps
p90 = 1.0
tau = 2500.0
transient = 500.0
repetition = 1e6 # us
print "\n*** *** ***\n"
print "CONFIGURING TRANSMITTER..."
Hahn_echo_ph.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
print "\nTRANSMITTER CONFIGURED."
print "***"
print "CONFIGURING RECEIVER..."
acq_time = Hahn_echo_ph.configureRX(SW_kHz, nPoints, nScans, nEchoes, nPhaseSteps) #ms
print "\nRECEIVER CONFIGURED."
print "***"
print "\nINITIALIZING PROG BOARD...\n"
Hahn_echo_ph.init_ppg();
print "\nLOADING PULSE PROG...\n"
Hahn_echo_ph.load([
    ('marker','start',nScans),
    ('phase_reset',1),
    ('pulse',p90,'ph1',r_[0,1,2,3]),
    ('delay',tau),
    ('pulse',2.0*p90,'ph2',r_[0,2]),
    ('delay',transient),
    ('acquire',acq_time),
    ('delay',repetition),
    ('jumpto','start'),
    ])
print "\nSTOPPING PROG BOARD...\n"
Hahn_echo_ph.stop_ppg();
print "\nRUNNING PROG BOARD...\n"
Hahn_echo_ph.runBoard();
data_length = 2*nPoints*nEchoes*nPhaseSteps
raw_data = Hahn_echo_ph.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
print "EXITING..."
print "\n*** *** ***\n"
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
data.ft('t',shift=True)
fl.next('FT raw data')
fl.plot(data.real,alpha=0.8)
fl.plot(data.imag,alpha=0.8)
fl.show()

