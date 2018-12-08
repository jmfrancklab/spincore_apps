import Hahn_echo
adcOffset = 45
carrierFreq_MHz = 2.0
tx_phase = 0.0
amplitude = 1.0
SW_kHz = 200.0
nPoints = 16384
nScans = 5 
p90 = 15.0
tau = 1000000.0
print "CONFIGURING TRANSMITTER..."
Hahn_echo.configureTX(adcOffset, carrierFreq_MHz, tx_phase, amplitude, nPoints)
print "\nTRANSMITTER CONFIGURED."
print "***"
print "CONFIGURING RECEIVER..."
acq_time = Hahn_echo.configureRX(SW_kHz, nPoints, nScans) #ms
print "\nRECEIVER SET."
print "***"
print "PROGRAMMING BOARD..."
Hahn_echo.programBoard(nScans,p90,tau)
print "\nBOARD PROGRAMMED."
print "***"
print "RUNNING BOARD..."
Hahn_echo.runBoard(acq_time)
print "EXITING..."
