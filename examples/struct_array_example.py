from pylab import *
from pyspecdata import *
# create a dtype for a structured array with 2 values, labeled as start_time and stop_time
times_dtype = dtype([('start_time',double),('stop_time',double)])
mytimes = zeros(10, dtype=times_dtype) # where before we call "zeros" or
#                                        "empty", we still do that, but feed it
#                                        a dtype argument to let it know this
#                                        is a structured array with multiple
#                                        fields
# now, whenever we set an element, we can specify not just the indices (here
# the colon), but also the field
mytimes[:]['start_time'] = r_[0:10]
mytimes[:]['stop_time'] = r_[0:10] + 1
mydata = nddata(r_[0:10]*10,[-1],['t'])
# I can attach my structured array just like any other normal axis
mydata.setaxis('t', mytimes)
mydata.name('data')
mydata.hdf5_write('struct_array_axis_example.h5')
mydata_read = nddata_hdf5('struct_array_axis_example.h5/data')
# now access the start vs. stop times
print("start times:",mydata_read.getaxis('t')['start_time'])
print("stop times:",mydata_read.getaxis('t')['stop_time'])
