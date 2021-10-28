import os, time, h5py
import pylab as plt
from numpy import empty
from matplotlib.ticker import FuncFormatter
import matplotlib.transforms as transforms
from pyspecdata import *
from pyspecProcScripts import *
from pyspecProcScripts import lookup_table
logger = init_logging("info")
signal_pathway = {'ph1':1}
fl=fl_mod()
filename='211029_6mM_TEMPOL_test_1'
f_slice=(-1e3,1e3)
t_range=(0,200)
@FuncFormatter
def thetime(x,position):
    result = time.localtime(x)
    return time.strftime('%I:%M%p',result)
with h5py.File(filename +'.h5','r') as f:
    log_grp = f['log']
    dset = log_grp['log']
    print("length of dset",dset.shape)
    #{{{convert to a proper structured array
    read_array = empty(len(dset),dtype=dset.dtype)
    read_array[:] = dset
    #}}}
    read_dict={}
    for j in range(dset.attrs['dict_len']):
        val = dset.attrs['val%d'%j]
        if isinstance(val, bytes):
            val = val.decode('ASCII')
        read_dict[dset.attrs['key%d'%j]] = val
for j in range(len(read_array)):
    thistime,thisrx,thispower,thiscmd = read_array[j]
    print('%-04d'%j,time.strftime('%Y-%m-%d %H:%M:%S',time.loacaltime(thistime)),
            thisrx,
            thispower,
            read_dict[thiscmd])
for filename,nodename,file_location in [
        (filename,'enhancement_curve','ODNP_NMR_comp/test_equipment')
        ]:
    s = find_file(filename,exp_type=file_location, expno=nodename)
    s.setaxis('indirect',r_[0:len(s.getaxis('indirect'))])
    s.chunk('t',['ph1','t2'],[4,-1])
    s.set_units('t2','s')
    s.labels({'ph1':r_[0.,1.,2.,3.]/4})
    s.ft('t2',shift=True)
    s.ft(['ph1'],unitary=True)
    s.reorder(['ph1','indirect'])
    DCCT(s,fl.next('Raw Data'))
    s.ift('t2')
    s.ift(['ph1'])
    t_start = t_range[-1]/4
    t_start *= 3
    rx_offset_corr = s['t2':(t_start,None)]
    rx_offset_corr = rx_offset_corr.data.mean()
    s -= rx_offset_corr
    s.ft('t2')
    s.ft(['ph1'])
    s = s['t2':f_slice]
    print(s.getaxis(indirect))
    fl.show()

