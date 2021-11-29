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
Ep_signal_pathway = {'ph1':1}
fl=fl_mod()
filename='211124_10mM_TEMPOL_test_1log'
file_location = 'ODNP_NMR_comp/ODNP'
Ep_f_slice=(-1e3,1e3)
IR_f_slice=(-1e3,1e3)
t_range = (0,0.2)
excluded_pathways = [(0,0)]

#{{{IR processing
for nodename, postproc, signal_pathway, clock_correction in [
        ('FIR_27dBm','spincore_IR_v1',{'ph1':0,'ph2':1},False),
        ('FIR_30dBm','spincore_IR_v1',{'ph1':0,'ph2':1},False),
        ('FIR_32dBm','spincore_IR_v1',{'ph1':0,'ph2':1},False),
        ('FIR_33dBm','spincore_IR_v1',{'ph1':0,'ph2':1},False),
        ]:
    IR = find_file(filename,exp_type=file_location,expno=nodename,
            postproc=postproc,lookup=lookup_table,fl=fl)
    times = IR['indirect':-1]
    IR.mean('indirect')
    fl.next('Raw IR')
    fl.image(IR.C.setaxis('vd','#').set_units('vd','scan #'))
    #fl.show();quit()
    IR['ph2',0]['ph1',0]['t2':0]=0 #kill axial noise
    IR.ift('t2')
    IR.ift(['ph1','ph2'])
    t_start = t_range[-1]/4
    t_start *= 3
    rx_offset_corr = IR['t2':(t_start,None)]
    rx_offset_corr = rx_offset_corr.data.mean()
    IR -= rx_offset_corr
    IR.ft('t2')
    IR.ft(['ph1','ph2'])
    zero_crossing = abs(select_pathway(IR['t2':IR_f_slice],signal_pathway)).C.sum('t2').argmin('vd',raw_index=True).item()
    IR=IR['t2':IR_f_slice]
    if 'nScans' in IR.dimlabels:
        IR.mean('nScans')
    IR.ift('t2')
    #{{{clock correction
    if clock_correction:
        clock_corr = nddata(np.linspace(-3,3,2500),'clock_corr')
        IR.ft('t2')
        if fl is not None:
            fl.next('before clock correction')
            fl.image(IR.C.setaxis('vd','#').set_units('vd','scan #'))
        s_clock=IR['ph1',1]['ph2',0].sum('t2')
        IR.ift(['ph1','ph2'])
        min_index = abs(s_clock).argmin('vd',raw_index=True).item()
        s_clock *= np.exp(-1j*clock_corr*IR.fromaxis('vd'))
        s_clock['vd',:min_index+1] *=-1
        s_clock.sum('vd').run(abs)
        if fl is not None:
            fl.next('clock correction')
            fl.plot(s_clock,'.',alpha=0.7)
        clock_corr = s_clock.argmax('clock_corr').item()
        plt.axvline(x=clock_corr, alpha=0.5, color='r')
        IR *= np.exp(-1j*clock_corr*IR.fromaxis('vd'))
        IR.ft(['ph1','ph2'])
        if fl is not None:
            fl.next('after auto-clock correction')
            fl.image(IR.C.setaxis('vd','#'))
        IR.ift('t2')
    #}}}
    #{{{phasing
    IR /= zeroth_order_ph(select_pathway(IR,signal_pathway))
    if 'nScans' in IR.dimlabels:
        IR.mean('nScans')
    IR.ft('t2')
    mysgn = determine_sign(select_pathway(IR.C.mean('vd'),signal_pathway))
    IR.ift('t2')
    best_shift = hermitian_function_test(select_pathway(IR.C.mean('vd')*mysgn,
        signal_pathway),aliasing_slop=1)
    IR.setaxis('t2',lambda x: x-best_shift).register_axis({'t2':0})
    IR.ft('t2')
    fl.next('Phase corrected')
    fl.image(IR.C.setaxis('vd','#').set_units('vd','scan #'))
    #}}}
    #{{{Alignment
    mysgn = determine_sign(select_pathway(IR['t2':IR_f_slice],signal_pathway))
    IR.ift(['ph1','ph2'])
    opt_shift,sigma, my_mask = correl_align(IR.C*mysgn,indirect_dim='vd',
            signal_pathway=signal_pathway)
    IR.ift('t2')
    IR *= np.exp(-1j*2*pi*opt_shift*IR.fromaxis('t2'))
    IR.ft('t2')
    IR.ift('t2')
    IR.ft(['ph1','ph2'])
    IR.ft('t2')
    IR.reorder(['ph1','ph2','vd','t2'])
    fl.next('Aligned')
    fl.image(IR.C.setaxis('vd','#').set_units('vd','scan #'))
    #}}}
    IR.ift('t2')
    #{{{FID slice
    d=IR.C
    d = d['t2':(0,None)]
    d['t2':0] *= 0.5
    d.ft('t2')
    fl.next('FID sliced')
    fl.image(d.C.setaxis(
'vd','#').set_units('vd','scan #'))
    #}}}
    #{{{Integrate with error
    error_pathway = (set(((j,k) for j in range(ndshape(d)['ph1']) for k in range(ndshape(d)['ph2'])))
            - set(excluded_pathways)
            -set([(signal_pathway['ph1'],signal_pathway['ph2'])]))
    error_pathway = [{'ph1':j,'ph2':k} for j,k in error_pathway]
    s_int,frq_slice = integral_w_errors(d,signal_pathway,error_pathway,
            convolve_method='Gaussian',
            indirect='vd',return_frq_slice=True)
    fl.next('1D diagnostic')
    fl.plot(select_pathway(d,signal_pathway))
    plt.axvline(x=frq_slice[0])
    plt.axvline(x=frq_slice[-1])
    #}}}
    s_int*= -1
    fl.next('IR %s'%nodename)
    fl.plot(s_int,'ko',capsize=2,alpha=0.3)
    #}}}
    fl.show()
#{{{Load/process enhancement
for filename,nodename,file_location in [
        (filename,'enhancement_curve','ODNP_NMR_comp/ODNP')
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
    zero_crossing = abs(s['t2':Ep_f_slice]['ph1':1]).C.sum('t2').argmin('time',raw_index=True).item()
    s = s['t2':Ep_f_slice] 
    s.ift('t2')
    #{{{phasing
    s /= zeroth_order_ph(select_pathway(s,Ep_signal_pathway))
    if 'nScans' in s.dimlabels:
        s.mean('nScans')
    s.ft('t2')
    mysgn = determine_sign(select_pathway(s,Ep_signal_pathway))
    s.ift('t2')
    best_shift = hermitian_function_test(select_pathway(s.C.mean('time')*mysgn,
        Ep_signal_pathway),aliasing_slop=1)
    s.setaxis('t2',lambda x: x-best_shift).register_axis({'t2':0})
    s.ft('t2')
    fl.next('phase corrected')
    fl.image(s.C.setaxis(
'time','#').set_units('time','scan #'))
    #}}}
    #{{{Alignment
    mysgn = determine_sign(select_pathway(s['t2':Ep_f_slice],Ep_signal_pathway))
    s.ift(['ph1'])
    opt_shift,sigma, my_mask = correl_align(s.C*mysgn,indirect_dim='time',
            signal_pathway=Ep_signal_pathway)
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
    #}}}
    s.ift('t2')
    #{{{FID slice
    d=s.C
    d = d['t2':(0,None)]
    d['t2':0] *= 0.5
    d.ft('t2')
    fl.next('FID sliced')
    fl.image(d.C.setaxis(
'time','#').set_units('time','scan #'))
    #}}}
    #{{{Integrate with error
    error_pathway = (set(((j) for j in range(ndshape(d)['ph1'])))
            - set(excluded_pathways)
            -set([(Ep_signal_pathway['ph1'])]))
    error_pathway = [{'ph1':j} for j in error_pathway]
    s_int,frq_slice = integral_w_errors(d,Ep_signal_pathway,error_pathway,
            convolve_method='Gaussian',
            indirect='time',return_frq_slice=True)
    fl.next('1D diagnostic')
    fl.plot(select_pathway(d,Ep_signal_pathway))
    plt.axvline(x=frq_slice[0])
    plt.axvline(x=frq_slice[-1])
    #}}}
    #{{{Normalize and flip
    time_axis = s_int.getaxis('time')
    #time_axis[0] = s.get_prop('start_time')
    #ini_time = time_axis[0]
    time_axis[-1] = s.get_prop('stop_time')    
    #for j in range(len(s_int.getaxis('time'))):
    #    time_axis[j] -= ini_time
    s_int.setaxis('time',time_axis)
    #}}}
    s_int /= np.real(s_int['time',0:1].data.item())
    s_int['time',zero_crossing+1:] *= -1
    fl.next('E(p)')
    fl.plot(s_int['time',:-3],'ko',capsize=2,alpha=0.3)
    fl.plot(s_int['time',-3:],'ro',capsize=2,alpha=0.3)
    #}}}
#{{{create nddata of power vs time from log
with h5py.File(search_filename(filename+".h5",exp_type='ODNP_NMR_comp/ODNP',unique=True),'r') as f:
    log_grp = f['Ep_log']
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
relative_time = read_array['time'] #- ini_time
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
fl.next('power axis W')
coupler_atten = 22
power_axis.data = (10**((power_axis.data+coupler_atten)/10+3))/1e6 #convert to W
fl.plot(power_axis,'.')
#}}}
#{{{finding average power over steps
dnp_time_axis = s_int.C.getaxis('time').copy()
dnp_time_axis = r_[dnp_time_axis,power_axis.getaxis('time')[-1]]
nddata_time_axis = nddata(dnp_time_axis,[-1],['time'])
slop=3.0
new_time_axis = nddata_time_axis.C.data
new_time_axis = nddata(new_time_axis,[-1],['time'])
power_vs_time = ndshape(nddata_time_axis).alloc().set_units('time','s')
power_vs_time.set_error(0)
power_vs_time.setaxis('time',new_time_axis.data)
#{{{find values for Ep
for j,(time_start,time_stop) in enumerate(zip(dnp_time_axis[1:],dnp_time_axis[2:-1])):
    if time_stop == dnp_time_axis[-2]:
        power_vs_time['time',j+1] = power_axis['time':((time_start),(time_stop))].mean('time',std=True)
    else:    
        power_vs_time['time',j+1] = power_axis['time':((time_start),(time_stop-2.5*slop))].mean('time',std=True)
    plt.axvline(x=time_start,color='k',alpha=0.5)
    if time_stop == dnp_time_axis[-2]:
        plt.axvline(x=time_stop,color='b',alpha=0.5)
    else:    
        plt.axvline(x=time_stop-(2.5*slop),color='b',alpha=0.5)
power_vs_time.set_units('time','s')
power_vs_time.data[0] = 0
power_vs_time = power_vs_time['time',:-1]
fl.plot(power_vs_time,'ro',capsize=6,human_units=False)
#}}}
#{{{set time axis to power for Ep
s_int.rename('time','power')
power_axis = np.real(power_vs_time.data)
s_int.setaxis('power',power_axis)
s_int.set_error('power',power_vs_time.get_error())
s_int = s_int['power',:-1] #taking out point from when it was added in in line 143 for the last power in the power axis
fl.next('Final E(p)')
fl.plot(np.real(s_int['power',:-3]),'ko',capsize=6,alpha=0.3)
fl.plot(np.real(s_int['power',-3:]),'ro',capsize=6,alpha=0.3)
#}}}
fl.show();quit()

