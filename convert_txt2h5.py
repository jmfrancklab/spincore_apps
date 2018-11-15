from pyspecdata import *
import os
import sys
def pull_data(directory,file_name):
    #{{{ documentation
    r'''use this function to pull data from a text file
    generated as the output by SpinCore and return the data
    as a list as well as the time axis as an ndarray.
    PARAMETERS
    ========== 
    directory : str
    
        Directory in which you will find the SpinCore raw
        data (.txt) file
        
    file_name : str
    
        Name of the SpinCore raw data (.txt) file

    RETURNS 
    ======= 
    result : list
    
        The raw data (amplitude) in a list, with elements of
        datatype complex128.

           
    time_axis : ndarray
    
        The correct time axis for the data, generated from
        the '*_params.txt' file of the raw data.


    '''
    #}}}
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
    return result, time_axis

directory = str(os.path.dirname(os.path.realpath(__file__)))
file_name = "181114_sweep1_SE1"
date = "181114"
name = "sweep1"
if "sweep" in name:
    field_sweep = True
if field_sweep:
    field_axis = linspace(3400.,3419.,20)
    for index,field in enumerate(field_axis):
        file_name = date+'_'+name+'_'+'SE%d'%(index+1)
        result, time_axis = pull_data(directory,file_name)
        if(index==0):
            data = ndshape

result, time_axis = pull_data(directory, file_name)
#field_sweep = True
#field_axis = linspace(3400.,3419.,20)
#if field_sweep:
    #data = ndshape([shape(result),len(field_axis)],['t','field']).alloc(dtype=complex128)
    #data = nddata([array(result),array(field_axis)],['t','field'])
#print ndshape(data)
#quit()
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
fl.next('test plot, time')
fl.plot(data)
data.ft('t',shift=True)
fl.next('test plot, freq')
fl.plot(data)
fl.show()
