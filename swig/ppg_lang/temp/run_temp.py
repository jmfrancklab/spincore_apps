import ppg_temp
date = '181210'
output_name = 'testing'
adcOffset = 48
carrierFreq_MHz = 14.46
tx_phase = 0.0
amplitude = 1.0
nPoints = 1024
nScans = 1
nEchoes = 1
print "\n*** *** ***\n"
print "CONFIGURING TRANSMITTER..."
ppg_temp.configureTX(adcOffset, carrierFreq_MHz, tx_phase, amplitude, nPoints)
print "\nTRANSMITTER CONFIGURED."
print "***"
print "\nINITIALIZING PROG BOARD...\n"
ppg_temp.init_ppg();
print "\nLOADING PULSE PROG..."
ppg_temp.load([
    ('marker','start',3),
    ('pulse',2.0,0), # this breaks the looping
    #('delay',1.0),
    #('pulse',2.0,0), # this breaks the looping
    ('delay',10e6),
    ('jumpto','start'),
    ])
print "\nSTOPPING PROG BOARD...\n"
ppg_temp.stop_ppg();
print "\nRUNNING PROG BOARD...\n"
ppg_temp.runBoard();
