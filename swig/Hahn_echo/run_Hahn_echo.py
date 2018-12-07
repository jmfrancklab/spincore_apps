import Hahn_echo
adcOffset = 45
carrierFreq_MHz = 2.0
tx_phase = 0.0
amplitude = 1.0
nScans = 5 
p90 = 15.0
tau = 1000000.0
print "CONFIGURING BOARD..."
Hahn_echo.configureBoard(adcOffset, carrierFreq_MHz, tx_phase, amplitude)
print "\nBOARD CONFIGURED."
print "***"
print "PROGRAMMING BOARD..."
Hahn_echo.programBoard(nScans,p90,tau)
print "\nBOARD PROGRAMMED."
print "***"
print "RUNNING BOARD..."
Hahn_echo.runBoard()
print "EXITING..."
