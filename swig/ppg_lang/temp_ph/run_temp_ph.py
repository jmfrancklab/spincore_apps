import ppg_temp_ph

date = '181210'
output_name = 'testing'
adcOffset = 48
carrierFreq_MHz = 5.0 
phase1 = 0.0
phase2 = 90.0
phase3 = 180.0
phase4 = 270.0
nPhases = 4 
amplitude = 1.0
nPoints = 1024
nScans = 1
nEchoes = 1
print "\n*** *** ***\n"
print "CONFIGURING TRANSMITTER..."
ppg_temp_ph.configureTX(adcOffset, carrierFreq_MHz, phase1, phase2, phase3, phase4, nPhases, amplitude, nPoints)
print "\nTRANSMITTER CONFIGURED."
print "***"
print "\nINITIALIZING PROG BOARD...\n"
ppg_temp_ph.init_ppg();
print "\nLOADING PULSE PROG..."
ppg_temp_ph.load([
    ('phase_reset',1),
    ('marker','start',3),
    ('pulse',1.0,0),
    ('delay',1.5),
    ('pulse',1.0,0),
    ('delay',1.5),
    ('pulse',1.0,0),
    ('delay',1.5),
    ('pulse',1.0,0),
    ('delay',1e6),
    ('jumpto','start'),
    ])
print "\nSTOPPING PROG BOARD...\n"
ppg_temp_ph.stop_ppg();
print "\nRUNNING PROG BOARD...\n"
ppg_temp_ph.runBoard();
