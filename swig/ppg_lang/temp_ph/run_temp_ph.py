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

from numpy import *
import ppg_temp_ph

date = '181210'
output_name = 'testing'
adcOffset = 48
carrierFreq_MHz = 5.0 
tx_phases = r_[0.0,90.0,180.0,270.0]
nPhases = 4 
amplitude = 1.0
nPoints = 1024
nScans = 1
nEchoes = 1
print "\n*** *** ***\n"
print "CONFIGURING TRANSMITTER..."
ppg_temp_ph.configureTX(adcOffset, carrierFreq_MHz, tx_phases, amplitude, nPoints)
print "\nTRANSMITTER CONFIGURED."
print "***"
print "\nINITIALIZING PROG BOARD...\n"
ppg_temp_ph.init_ppg();
print "\nLOADING PULSE PROG..."
ppg_temp_ph.load([
    ('marker','start',1),
    ('phase_reset',1),
    ('pulse',2.0,'ph1',r_[0,1]),
    ('delay',1.5),
    ('pulse',2.0,'ph1',r_[2,3]),
    ('delay',10e6),
    ('jumpto','start'),
    ])
print "\nSTOPPING PROG BOARD...\n"
ppg_temp_ph.stop_ppg();
print "\nRUNNING PROG BOARD...\n"
ppg_temp_ph.runBoard();
