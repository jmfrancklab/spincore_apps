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
filename='211102_500uM_TEMPOL_test_final'
f_slice=(-0.5e3,0.5e3)
t_range=(0,0.1)
excluded_pathways = [(0,0)]
#{{{Load/process enhancement
for filename,nodename,file_location in [
        (filename,'enhancement_curve','ODNP_NMR_comp/test_equipment')
        ]:
    s = find_file(filename,exp_type=file_location, expno=nodename)
    s.ft('t2',shift=True)
    s.ft(['ph1'])
    s.reorder(['ph1','indirect'])
    s_start = s.getaxis('indirect')[0]
    fl.next('Raw')
    fl.image(s.C.setaxis(
'indirect','#').set_units('indirect','scan #'))
    s.ift('t2')
    fl.next('raw time')
    fl.image(s.C.setaxis(
'indirect','#').set_units('indirect','scan #'))
    s.rename('indirect','time')
    s.ft('t2')
    zero_crossing = abs(s['t2':f_slice]['ph1':1]).C.sum('t2').argmin('time',raw_index=True).item()
    #}}}
    s = s['t2':f_slice] 
    s.ift('t2')
    s /= zeroth_order_ph(select_pathway(s,signal_pathway))
    s.mean('nScans')
    s.ft('t2')
    s.ift('t2')
    best_shift = hermitian_function_test(select_pathway(s.C.mean('time'),signal_pathway),
            aliasing_slop=1)
    s.setaxis('t2',lambda x: x-best_shift).register_axis({'t2':0})
    s.ft('t2')
    fl.next('phase corrected')
    fl.image(s.C.setaxis(
'time','#').set_units('time','scan #'))
    mysgn = determine_sign(select_pathway(s['t2':f_slice],signal_pathway))
    s.ift(['ph1'])
    opt_shift,sigma, my_mask = correl_align(s*mysgn,indirect_dim='time',
            signal_pathway=signal_pathway)
    s.ift('t2')
    s *= np.exp(-1j*2*pi*opt_shift*s.fromaxis('t2'))
    s.ft('t2')
    s.ift('t2')
    s.ft(['ph1'])
    s.ft('t2')
    s.reorder(['ph1','time','t2'])
    fl.next('Aligned')
    fl.image(s.C.setaxis(
'time','#').set_units('time','scan #'))
    ph0 = s.C.sum('t2')
    s.ift('t2')
    ph0 /= abs(ph0)
    s /= ph0
    d=s.C
    d = d['t2':(0,None)]
    d['t2':0] *= 0.5
    d.ft('t2')
    fl.next('FID sliced')
    fl.image(d.C.setaxis(
'time','#').set_units('time','scan #'))
    error_pathway = (set(((j) for j in range(ndshape(d)['ph1'])))
            - set(excluded_pathways)
            -set([(signal_pathway['ph1'])]))
    error_pathway = [{'ph1':j} for j in error_pathway]
    s_int,frq_slice = integral_w_errors(d,signal_pathway,error_pathway,
            convolve_method='Gaussian',
            indirect='time',return_frq_slice=True)
    fl.next('1D diagnostic')
    fl.plot(select_pathway(d,signal_pathway))
    plt.axvline(x=frq_slice[0])
    plt.axvline(x=frq_slice[-1])
    #{{{move first point to a more reasonable placement so we actually see the curve
    #}}}
    #{{{Normalize and flip
    s_int /= np.real(s_int['time',0].data.item())
    s_int['time',1:] *= -1
    ini_time = s_int.C.getaxis('time')[1] - (s_int.C.getaxis('time')[-1]-s_int.C.getaxis('time')[-2])
    time_axis = s_int.getaxis('time')
    time_axis[0] = ini_time
    s_int.setaxis('time',time_axis)
    print(s_int['time',:])
    print(ini_time)
    for j in range(len(s_int.getaxis('time'))):
        time_axis[j] -= ini_time
    #}}}
    fl.next('E(p)')
    fl.plot(s_int['time',:-3],'ko',capsize=2,alpha=0.3)
    fl.plot(s_int['time',-3:],'ro',capsize=2,alpha=0.3)
#{{{create nddata of power vs time from log
with h5py.File("211102_500uM_TEMPOL_test_final.h5",'r') as f:
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
power_axis = nddata(read_array['power'],[-1],['time'])
power_axis.setaxis('time',relative_time)
fl.next('power axis')
fl.plot(power_axis,'.')
power_axis = nddata(read_array['power'],[-1],['time'])
power_axis.setaxis('time',relative_time)
power_axis.name('power')
fl.next('power axis')
fl.plot(power_axis,'.')
#}}}
#{{{finding average power over steps
dnp_time_axis = list(s_int.getaxis('time'))
power_list = []
for time_start,time_stop in zip(dnp_time_axis[:-1],dnp_time_axis[1:]):
    power_list.append(power_axis['time':(time_start,time_stop)].mean('time'))
    plt.axvline(x=time_start)
for j in range(len(power_list)):
    s_int.getaxis('time')[j] = power_list[j].data
s_int.rename('time','power (dBm)')
fl.next('final E(p)')
fl.plot(s_int['power (dBm)',:-3],'ko',capsize=2,alpha=0.3)
fl.plot(s_int['power (dBm)',-3:],'ro',capsize=2,alpha=0.3)
fl.show()

