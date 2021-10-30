import os, time, h5py
import pylab as plt
from numpy import empty
from matplotlib.ticker import FuncFormatter
import matplotlib.transforms as transforms
from pyspecdata import *
from pyspecProcScripts import *
from pyspecProcScripts import lookup_table
from Instruments.logobj import logobj
logger = init_logging("info")
signal_pathway = {'ph1':1}
fl=fl_mod()
filename='211029_500uM_TEMPOL_test_1'
f_slice=(-1e3,1e3)
t_range=(0,200)
with h5py.File('211029_500uM_TEMPOL_test_1.h5','r') as f:
    log_grp = f['log']
    thislog = logobj()
    thislog.__setstate__(log_grp)
    read_array = thislog.total_log
    read_dict = thislog.log_dict
for j in range(len(read_array)):
    thistime,thisrx,thispower,thiscmd = read_array[j]
fig, (ax_Rx,ax_power) = plt.subplots(2,1, figsize=(10,8))
fl.next("log figure",fig=fig)
ax_Rx.set_ylabel('Rx/mV')
start_time = read_array['time'][0]
relative_time = read_array['time'] - start_time
ax_Rx.plot(relative_time, read_array['Rx'],'.')
ax_power.set_ylabel('power/dBm')
ax_power.plot(relative_time,read_array['power'],'.')
mask = read_array['cmd'] != 0
n_events = len(relative_time[mask])
trans_power = transforms.blended_transform_factory(
        ax_power.transData,ax_power.transAxes)
trans_Rx = transforms.blended_transform_factory(
        ax_Rx.transData, ax_Rx.transAxes)
for j, thisevent in enumerate(read_array[mask]):
    ax_Rx.axvline(x=thisevent['time']-start_time)
    ax_power.axvline(x=thisevent['time']-start_time)
    y_pos = j/n_events
    ax_Rx.text(thisevent['time']-start_time,y_pos,read_dict[thisevent['cmd']],transform=trans_Rx)
    ax_power.text(thisevent['time']-start_time,y_pos,read_dict[thisevent['cmd']],transform=trans_power)
ax_power.legend(**dict(bbox_to_anchor=(1.05,1),loc=2,borderaxespad=0.))
plt.tight_layout()
Rx_stuff = nddata(read_array['Rx'],[-1],['Rx'])
time_axis = nddata(relative_time,[-1],['t2'])
print(ndshape(Rx_stuff))
print(ndshape(time_axis))
Rx_stuff *= time_axis
print(ndshape(Rx_stuff))
fl.next('Rx')
fl.plot(Rx_stuff,'.')

for filename,nodename,file_location in [
        (filename,'enhancement_curve','ODNP_NMR_comp/test_equipment')
        ]:
    s = find_file(filename,exp_type=file_location, expno=nodename)
    s.setaxis('indirect',lambda x: x-start_time) # convert to a relative time axis:w
    s.ft('t2',shift=True)
    #s.ft(['ph1'],unitary=True)
    s.reorder(['ph1','indirect'])
    fl.next('Raw')
    fl.image(s)
    s.ift('t2')
    fl.next('raw time')
    fl.image(s)
    fl.show();quit()
    #DCCT(s,fl.next('Raw Data'))
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

