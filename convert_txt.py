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
for line in F:
    temp = line.strip().split()
    real.append(float(temp[0]))
    imag.append(float(temp[1]))
    #real = temp[0]
    #imag = temp[1]
    #result.append(temp[0]+1j*temp[1])
F.close()
print real[0]
print imag[0]
print size(real)
print size(imag)
real = complex128(real)
imag = complex128(imag)
result = complex128(real + 1j*imag) 
print result[0]
print real[0]
print imag[0]
print shape(result)
SW = 60e3 # get this to be read in, i.e. print in the
            # text file output from SpinCore program
acq_time = float(size(real))/SW
print acq_time
#data = nddata(result,'data',
#result = complex128(result)
#print ndshape(data)
