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
F.close()
num_points = float(shape(result)[0])
SW = 60e3 # get this to be read in, i.e. print in the
            # text file output from SpinCore program
acq_time = num_points/SW
print "ACQUISITION TIME:",acq_time
dt = acq_time/num_points
print "DWELL TIME:",dt
time_axis = linspace(0.0,acq_time,num_points)
data = nddata(array(result),'t')
data.setaxis('t',time_axis)
data.set_units('t','s')
data.name('signal')
date = '181109'
id_string = 'HahnEcho'
data.hdf5_write(date+'_'+id_string+'.h5')
print "name of data",data.name()
print "units should be",data.get_units('t')
print "shape of data",ndshape(data)
#fl = figlist_var()
#fl.next('test plot')
#fl.plot(data)
#fl.show()
