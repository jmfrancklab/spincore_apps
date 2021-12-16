import os, time, h5py
import pylab as plt
from numpy import empty
from sympy import exp as s_exp
from sympy import symbols, Symbol
from matplotlib.ticker import FuncFormatter
import matplotlib.transforms as transforms
from pyspecdata import *
from pyspecProcScripts import *
from pyspecProcScripts import lookup_table
from Instruments.logobj import logobj
logger = init_logging("info")
fl=fl_mod()
filename='211215_150uM_TEMPOL'
file_location = 'ODNP_NMR_comp/ODNP'
Ep_f_slice=(0.2e3,0.2e3)
Ep_t_range = (0,0.5)
Ep_signal_pathway = {'ph1':1}
t_center_echo = 0.0035
IR_f_slice=(-0.2e3,0.2e3)
t_range = (0,0.2)
IR_signal_pathway = {'ph1':0,'ph2':1}
excluded_pathways = [(0,0)]
R1w = 1/2.172
nPowers = 15
ppt = 1.5167e-3
C=0.15
#{{{load in log
with h5py.File(search_filename(filename+".h5",exp_type='ODNP_NMR_comp/ODNP',unique=True),'r') as f:
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
log_start_time = read_array['time'][0]
print("LOG START TIME IS:",log_start_time)
relative_time = read_array['time']
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
    ax_Rx.axvline(x=thisevent['time']-log_start_time)
    ax_power.axvline(x=thisevent['time']-log_start_time)
    y_pos = j/n_events
ax_power.legend(**dict(bbox_to_anchor=(1.05,1),loc=2,borderaxespad=0.))
plt.tight_layout()
power_axis = nddata(read_array['power'],[-1],['time'])
power_axis.setaxis('time',relative_time)
power_axis.setaxis('time',lambda x: x - log_start_time)
fl.next('power axis')
fl.plot(power_axis,'.')
power_axis.name('power')
fl.next('power axis W')
coupler_atten = 22
power_axis.data = (10**((power_axis.data+coupler_atten)/10+3))/1e6 #convert to W
fl.plot(power_axis,'.')
#}}}
#{{{IR processing
T1_list = []
power_list = []
start_times = []
stop_times = []
errors=[]
for nodename, postproc in [
        ('FIR_noPower','spincore_IR_v1'),
        #('FIR_27dBm','spincore_IR_v1'),
        #('FIR_30dBm','spincore_IR_v1'),
        #('FIR_32dBm','spincore_IR_v1'),
        #('FIR_33dBm','spincore_IR_v1'),
        ]:
    IR = find_file(filename,exp_type=file_location,expno=nodename,
            postproc=get_prop('acq_params')['IR_postproc'],lookup=lookup_table)
    times = IR.C.getaxis('indirect').copy()
    IR.mean('indirect')
    fl.next('Raw IR')
    fl.image(IR.C.setaxis('vd','#').set_units('vd','scan #'))
    IR['ph2',0]['ph1',0]['t2':0]=0 #kill axial noise
    if 'nScans' in IR.dimlabels:
        IR.mean('nScans')
    zero_crossing = abs(select_pathway(IR['t2':IR_f_slice],IR_signal_pathway)).C.sum('t2').argmin('vd',raw_index=True).item()
    IR=IR['t2':IR_f_slice]
    IR.ift('t2')
    #{{{phasing
    IR.setaxis('t2',lambda x: x-t_center_echo).register_axis({'t2':0})
    IR.ft('t2')
    IR.ift('t2')
    IR /= zeroth_order_ph(select_pathway(IR,IR_signal_pathway))
    IR.ft('t2')    
    #}}}
    IR.ift('t2')
    #{{{FID slice
    d=IR.C
    d = d['t2':(0,None)]
    d['t2':0] *= 0.5
    d.ft('t2')
    #}}}
    #{{{Integrate with error
    error_pathway = (set(((j,k) for j in range(ndshape(d)['ph1']) for k in range(ndshape(d)['ph2'])))
            - set(excluded_pathways)
            -set([(signal_pathway['ph1'],signal_pathway['ph2'])]))
    error_pathway = [{'ph1':j,'ph2':k} for j,k in error_pathway]
    s_int,frq_slice = integral_w_errors(d,signal_pathway,error_pathway,
            convolve_method='Lorentzian',
            indirect='vd',return_frq_slice=True)
    #}}}
    #{{{Fitting Routine
    x = s_int.fromaxis('vd')
    M0,Mi,R1,vd = symbols("M_0 M_inf R_1 vd",Real=True)
    functional_form = Mi + (M0-Mi) * s_exp(-vd*R1)
    f = fitdata(s_int)
    f.functional_form = functional_form
    f.fit()
    T1 = 1./f.output('R_1')
    fit = f.eval(100)
    T1_list.append(T1)
    #}}}
    #}}}
#{{{finding average power for each T1
    if nodename == 'FIR_noPower':
        pass
    else:
        start_time = IR.get_prop('start_time')-log_start_time
        stop_time = IR.get_prop('stop_time')-log_start_time
        avg_power = power_axis['time':(start_time,
            stop_time)].mean('time',std=True)
        errors.append(avg_power.get_error())
        power_list.append(avg_power)
        fl.next('power axis W')
        start_times.append(start_time)
        stop_times.append(stop_time)
        plt.axvline(x=start_time,color='k',alpha=0.5)
        plt.axvline(x=stop_time,color='b',alpha=0.5)
        nddata_p_vs_t = nddata(power_list,[-1],['time'])
        nddata_p_vs_t.setaxis('time',start_times)
        for j in range(len(power_list)):
            nddata_p_vs_t['time',j] = power_list[j]
        nddata_p_vs_t.set_error(errors)
        fl.plot(nddata_p_vs_t,'ro',capsize=6)
logger.info(strm("T1 list:",T1_list)) #we don't expect good T1s since bad tuning
logger.info(strm("Power list:",power_list))
#}}}
#{{{Load process enhancement
for filename,nodename,file_location in [
        (filename,'enhancement_curve','ODNP_NMR_comp/ODNP')
        ]:
    #{{{
    s = find_file(filename,exp_type=file_location, expno=nodename)
    s.ft('t2',shift=True)
    s.ft(['ph1'])
    s.reorder(['ph1','indirect'])
    fl.next('Raw Ep')
    fl.image(s.C.setaxis('indirect','#').set_units('indirect','scan #'))
    s['ph1',0]['t2':0] = 0 #kill axial noise
    s.rename('indirect','time')
    zero_crossing = abs(select_pathway(s['t2':Ep_f_slice],Ep_signal_pathway)).C.sum('t2').argmin('time',raw_index=True).item()
    s = s['t2':Ep_f_slice]
    if 'nScans' in s.dimlabels:
        s.mean('nScans')
    s.ift('t2')
    #}}}
    #{{{phasing
    s.setaxis('t2',lambda x: x-t_center_echo).register_axis({'t2':0})
    s.ft('t2')
    s.ift('t2')
    s /= zeroth_order_ph(select_pathway(s,Ep_signal_pathway))
    s.ft('t2')    
    #}}}
    s.ift('t2')
    #{{{FID slice
    d=s.C
    d = d['t2':Ep_t_range]
    d['t2':0] *= 0.5
    d.ft('t2')
    #}}}
    #{{{Integrate with error
    error_pathway = (set(((j) for j in range(ndshape(d)['ph1'])))
            - set(excluded_pathways)
            -set([(Ep_signal_pathway['ph1'])]))
    error_pathway = [{'ph1':j} for j in error_pathway]
    s_int,frq_slice = integral_w_errors(d,Ep_signal_pathway,error_pathway,
            convolve_method='Gaussian',
            indirect='time',return_frq_slice=True)
    #}}}
    #{{{set time axis
    s_int.getaxis('time')[:]['start_times'] -= log_start_time
    s_int.getaxis('time')[:]['stop_times'] -= log_start_time
    s_int.getaxis('time')[-1]['stop_times'] =power_axis.getaxis('time')[-1]
    time_axis = s_int.getaxis('time')[:]['start_times']
    s_int.setaxis('time',time_axis)
    #}}}
    #{{{Normalize and flip
    s_int['time',zero_crossing:] *= -1
    s_int /= np.real(s_int['time',0:1].data.item())
    fl.next('E(p) before power correction')
    fl.plot(s_int['time',:-3],'ko',capsize=2,alpha=0.3)
    fl.plot(s_int['time',-3:],'ro',capsize=2,alpha=0.3)
    #}}}
    #}}}
    #{{{finding average power over steps
    dnp_time_axis = s.C.getaxis('time').copy()
    dnp_time_axis[0]['stop_times'] = s.get_prop('thermal_done_time')+50
    dnp_time_axis[0]['start_times'] = s.get_prop('start_time')+10
    dnp_time_axis[:]['start_times'] -= log_start_time
    dnp_time_axis[:]['stop_times'] -= log_start_time
    nddata_time_axis = nddata(dnp_time_axis,[-1],['time'])
    new_time_axis = nddata_time_axis.C.data
    new_time_axis = nddata(new_time_axis,[-1],['time'])
    power_vs_time = ndshape(nddata_time_axis).alloc().set_units('time','s')
    power_vs_time.set_error(0)
    power_vs_time.setaxis('time',new_time_axis.data)
    #{{{find values for Ep
    fl.next('power axis W')
    for j,(time_start,time_stop) in enumerate(zip(dnp_time_axis[:]['start_times'],dnp_time_axis[:]['stop_times'])):
        power_vs_time['time',j] = power_axis['time':((time_start),(time_stop))].mean('time',std=True)
        power_vs_time.set_units('time','s')
        plt.axvline(x=time_start,color='red')
        plt.axvline(x=time_stop,color='blue')
    avg_p_vs_t = nddata(power_vs_time.data,[-1],['time'])
    avg_p_vs_t.set_error(power_vs_time.get_error())
    avg_p_vs_t.setaxis('time',dnp_time_axis[:]['start_times'])
    avg_p_vs_t.data[0] = 0
    avg_p_vs_t['time',0].set_error(0)
    fl.plot(avg_p_vs_t,'ro',capsize=6)
    #}}}
    #}}}
    #{{{set time axis to power for Ep
    s_int.rename('time','power')
    power_axis = np.real(power_vs_time.data)
    s_int.setaxis('power',power_axis)
    s_int.set_error('power',power_vs_time.get_error())
    idx_maxpower = np.argmax(s_int.getaxis('power'))
    enhancement=s_int
    fl.next('Final E(p)')
    fl.plot(np.real(s_int['power',:-3]),'ko',capsize=6,alpha=0.3)
    fl.plot(np.real(s_int['power',-3:]),'ro',capsize=6,alpha=0.3)
    #}}}
fl.show();quit()

