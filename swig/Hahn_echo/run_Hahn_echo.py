from pyspecdata import *
import os
import sys
import Hahn_echo
#{{{
fl = figlist_var()

#{{{ Verify arguments compatible with board
def verifyParams():
    if (nPoints > 16*1024 or nPoints < 1):
        print "ERROR: MAXIMUM NUMBER OF POINTS IS 16384."
        print "EXITING."
        quit()
    else:
        print "VERIFIED NUMBER OF POINTS."
    if (nScans < 1):
        print "ERROR: THERE MUST BE AT LEAST 1 SCAN."
        print "EXITING."
        quit()
    else:
        print "VERIFIED NUMBER OF SCANS."
    if (p90 < 0.065):
        print "ERROR: PULSE TIME TOO SMALL."
        print "EXITING."
        quit()
    else:
        print "VERIFIED PULSE TIME."
    if (tau < 0.065):
        print "ERROR: DELAY TIME TOO SMALL."
        print "EXITING."
        quit()
    else:
        print "VERIFIED DELAY TIME."
    return
#}}}
date = '181208'
output_name = 'test_echo_2'
adcOffset = 48
carrierFreq_MHz = 14.46
tx_phase = 0.0
amplitude = 1.0
SW_kHz = 50.0
nPoints = 1024
nScans = 1
nEchoes = 1
p90 = 1.0 # us
tau = 10500.0 # us
transient = 500.0 # us
repetition = 1000.0 # ms

#for tx_phase in [0.0, 90.0, 180.0, 270.0]:
#output_name = output_name + str(tx_phase)
verifyParams()
print "\n*** *** ***\n"
print "CONFIGURING TRANSMITTER..."
Hahn_echo.configureTX(adcOffset, carrierFreq_MHz, tx_phase, amplitude, nPoints)
print "\nTRANSMITTER CONFIGURED."
print "***"
print "CONFIGURING RECEIVER..."
acq_time = Hahn_echo.configureRX(SW_kHz, nPoints, nScans) #ms
print "\nRECEIVER CONFIGURED."
print "***"
print "PROGRAMMING BOARD..."
Hahn_echo.programBoard(nScans,p90,tau,acq_time,transient,repetition)
print "\nBOARD PROGRAMMED."
print "***"
print "RUNNING BOARD..."
Hahn_echo.runBoard()
data_length = 2*nPoints*nEchoes
raw_data = Hahn_echo.getData(data_length, nPoints, nEchoes, output_name)
print "EXITING..."
print "\n*** *** ***\n"
raw_data.astype(float)
data = []
data[::] = complex128(raw_data[0::2]+1j*raw_data[1::2])
#for x in xrange(shape(raw_data)[0]/2):
    #data.append(complex128(float(raw_data[x]))+1j*complex128(float(raw_data[x+1])))
print "COMPLEX DATA ARRAY LENGTH:",shape(data)[0]
print "RAW DATA ARRAY LENGTH:",shape(raw_data)[0]
time_axis = linspace(0.0,acq_time*1e-3,nPoints)
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

