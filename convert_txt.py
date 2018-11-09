from pyspecdata import *
import os
import sys
#dir_path = os.path.dirname(os.path.realpath(__file__))
#directory = "/Users/alecabeatonjr/gsyr/exp_data/test_equip"
directory = "C:\\apps-su\\spincore_apps"
file_name = "Hahn_echo"
F = open(directory+"\\"+file_name+".txt", "r")
real = []
imag = []
result = []
for line in F:
    temp = line.strip().split()
    result.append(complex128(float(temp[0]))+1j*complex128(float(temp[1])))
    #real.append(float(temp[0]))
    #imag.append(float(temp[1]))
F.close()
quit()
#result = complex128(real) + 1j*complex128(imag) 
if (complex128(real[0]) + 1j*complex128(imag[0]) != result[0]):
        raise ValueError('Quadrature data incorrectly cast to complex array')
print result[0]
print real[0]
print imag[0]
print shape(result)
SW = 60e3 # get this to be read in, i.e. print in the
            # text file output from SpinCore program
acq_time = float(size(real))/SW
print "ACQUISITION TIME:",acq_time
dt = acq_time/float(size(real))
print "DWELL TIME:",dt
time_axis = linspace(0.0,acq_time,float(size(real)))
data = nddata(result,'t')
data.setaxis('t',time_axis)
print data
fl = figlist_var()
fl.next('test plot')
fl.plot(data)
fl.show()
