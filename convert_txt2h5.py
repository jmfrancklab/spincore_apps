from pyspecdata import *
import os
import sys
def pull_data(directory,file_name,suppress_print = False):
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
    dt = acq_time/num_points
    if not suppress_print:
        print "ACQUISITION TIME:",acq_time
        print "DWELL TIME:",dt
    time_axis = linspace(0.0,acq_time,num_points)
    return result, time_axis

fl = figlist_var()
directory = str(os.path.dirname(os.path.realpath(__file__)))
#file_name = "181114_sweep1_SE1"
date = "181121"
name = "p90_200us"
file_name = date+'_'+name
field_sweep = False
if "sweep" in name:
    field_sweep = True
if field_sweep:
    field_axis = linspace(3407.5,3409.4,20)
    for index,field in enumerate(field_axis):
        file_name = date+'_'+name+'_'+'SE%d'%(index)
        result, time_axis = pull_data(directory,file_name,True)
        if(index==0):
            data = ndshape([len(field_axis),len(time_axis)],
                    ['field','t']).alloc(dtype=complex128)
            data.setaxis('t',time_axis).set_units('t','s')
            data.setaxis('field',field_axis)
        print "LOADING ... INDEX %d\tFIELD %0.2f"%(index,field)
        data['field',index] = result
if not field_sweep:
    result, time_axis = pull_data(directory, file_name)
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
        print "File already exists..."
        save_file = False
print "name of data",data.name()
print "units should be",data.get_units('t')
print "shape of data",ndshape(data)
fl.next('test plot, time')
if field_sweep:
    fl.plot(data['field',0],alpha=0.3)
    fl.plot(data['field',5],alpha=0.3)
    #fl.plot(data['field',15],alpha=0.3)
if not field_sweep:
    fl.plot(data)
    fl.plot(data.imag)
    data.ft('t',shift=True)
    fl.next('test plot, freq')
    fl.plot(data)
    fl.plot(data.imag)
fl.show()
