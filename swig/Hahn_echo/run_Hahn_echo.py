from pyspecdata import *
import os
import sys
import Hahn_echo
#{{{
fl = figlist_var()
def pull_data(id_string):
    F = open(str(os.path.dirname(os.path.realpath(__file__)))+"\\"+id_string+".txt", "r")
    real = []
    imag = []
    result = []
    for line in F:
        temp = line.strip().split()
        result.append(complex128(float(temp[0]))+1j*complex128(float(temp[1])))
    F.close()
    num_points = float(shape(result)[0])
    ACQ = nPoints/SW_kHz
    if nPoints/SW_kHz == acq_time:
        print "Acquisition time:",acq_time,"ms"
    else:
        print "Acquisition time conflict"
    if nPoints == num_points:
        print "Number of points:",nPoints
    else:
        print "Number of points conflict"
    dt = acq_time/nPoints
    print "Dwell time:",dt,"ms"
    time_axis = linspace(0.0,acq_time,nPoints)
    return result, time_axis
#}}}

date = '181207'
output_name = 'testing'
adcOffset = 45
carrierFreq_MHz = 2.0
tx_phase = 0.0
amplitude = 1.0
SW_kHz = 200.0
nPoints = 16384
nScans = 5 
nEchoes = 1
p90 = 15.0
tau = 1000000.0

for tx_phase in [0.0, 90.0, 180.0, 270.0]:
    #output_name = output_name + str(tx_phase)
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
    Hahn_echo.programBoard(nScans,p90,tau)
    print "\nBOARD PROGRAMMED."
    print "***"
    print "RUNNING BOARD..."
    Hahn_echo.runBoard(acq_time)
    data_length = 2*nPoints*nEchoes
    my_array = Hahn_echo.getData(data_length, nPoints, nEchoes, output_name)
    print "EXITING..."
    print "\n*** *** ***\n"
    print my_array
    quit()
    result, time_axis = pull_data(output_name)
    data = nddata(array(result),'t')
    data.setaxis('t',time_axis).set_units('t','s')
    data.name('signal')
    save_file = True
    while save_file:
        try:
            data.hdf5_write(date+'_'+name+'.h5')
            save_file = False
        except Exception as e:
            print e
            print "FILE ALREADY EXISTS."
            save_file = False
    print "name of data",data.name()
    print "units should be",data.get_units('t')
    print "shape of data",ndshape(data)
fl.next('raw data')
fl.plot(data.real,alpha=0.8)
fl.plot(data.imag,alpha=0.8)
data.ft('t',shift=True)
fl.next('FT raw data')
fl.plot(data.real,alpha=0.8)
fl.plot(data.imag,alpha=0.8)
fl.show()

