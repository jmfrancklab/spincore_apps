from pyspecdata import *
import os
import sys
directory = str(os.path.dirname(os.path.realpath(__file__)))
file_name = "181113_CPMG_5"
F = open(directory+"\\"+file_name+".txt", "r")
real = []
imag = []
result = []
for line in F:
    temp = line.strip().split()
    if temp[0] == 'SPECTRAL':
        SW = float(temp[-1])
    else:
            result.append(complex128(float(temp[0]))+1j*complex128(float(temp[1])))
F.close()
num_points = float(shape(result)[0])
acq_time = num_points/SW
print "ACQUISITION TIME:",acq_time
dt = acq_time/num_points
print "DWELL TIME:",dt
time_axis = linspace(0.0,acq_time,num_points)
data = nddata(array(result),'t')
data.setaxis('t',time_axis)
data.set_units('t','s')
data.name('signal')
save_file = True
while save_file:
    try:
        data.hdf5_write(file_name+'.h5')
        save_file = False
    except Exception as e:
        print e
        print "File already exists..."
        save_file = False
print "name of data",data.name()
print "units should be",data.get_units('t')
print "shape of data",ndshape(data)
fl = figlist_var()
fl.next('test plot')
fl.plot(data)
fl.show()
