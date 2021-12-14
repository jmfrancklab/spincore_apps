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
Ep_signal_pathway = {'ph1':1}
fl=fl_mod()
filename='211213_10mM_TEMPOL_test'
file_location = 'ODNP_NMR_comp/ODNP'
Ep_f_slice=(0.15e3,0.4e3)
IR_f_slice=(0.15e3,0.4e3)
Ep_t_range = (0,0.2)
t_range = (0,0.2)
excluded_pathways = [(0,0)]
R1w = 1/2.172
nPowers = 15
ppt = 1.5167e-3
C=0.01
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
    #ax_Rx.text(thisevent['time']-log_start_time,y_pos,read_dict[thisevent['cmd']],transform=trans_Rx)
    #ax_power.text(thisevent['time']-log_start_time,y_pos,read_dict[thisevent['cmd']],transform=trans_power)
ax_power.legend(**dict(bbox_to_anchor=(1.05,1),loc=2,borderaxespad=0.))
plt.tight_layout()
power_axis = nddata(read_array['power'],[-1],['time'])
power_axis.setaxis('time',relative_time)
power_axis.setaxis('time',lambda x: x - log_start_time)
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
#{{{IR processing
T1_list = []
power_list = []
start_times = []
stop_times = []
errors=[]
for nodename, postproc, signal_pathway, clock_correction in [
        ('FIR_noPower','spincore_IR_v1',{'ph1':0,'ph2':1},False),
        ('FIR_27dBm','spincore_IR_v1',{'ph1':0,'ph2':1},False),
        ('FIR_30dBm','spincore_IR_v1',{'ph1':0,'ph2':1},False),
        ('FIR_32dBm','spincore_IR_v1',{'ph1':0,'ph2':1},False),
        ('FIR_33dBm','spincore_IR_v1',{'ph1':0,'ph2':1},False),
        ]:
    IR = find_file(filename,exp_type=file_location,expno=nodename,
            postproc=postproc,lookup=lookup_table)
    times = IR.C.getaxis('indirect').copy()
    IR.mean('indirect')
    fl.next('Raw IR')
    fl.image(IR.C.setaxis('vd','#').set_units('vd','scan #'))
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
    IR.ft('t2')
    IR.ift('t2')
    best_shift = hermitian_function_test(select_pathway(IR.C.mean('vd'),
        signal_pathway),aliasing_slop=0)
    best_shift = 0.0035 #this data is bad (bad tuning) so I hard set the shift
    IR.setaxis('t2',lambda x: x-best_shift).register_axis({'t2':0})
    IR.ft('t2')
    IR.ift('t2')
    IR /= zeroth_order_ph(select_pathway(IR,signal_pathway))
    IR.ft('t2')    
    #}}}
    #{{{Alignment
    mysgn = determine_sign(select_pathway(IR['t2':IR_f_slice].C,signal_pathway))
    IR.ift(['ph1','ph2'])
    opt_shift,sigma, my_mask = correl_align(IR.C*mysgn,indirect_dim='vd',
            signal_pathway=signal_pathway,sigma=150)#again, bad data
    IR.ift('t2')
    IR *= np.exp(-1j*2*pi*opt_shift*IR.fromaxis('t2'))
    IR.ft('t2')
    IR.ift('t2')
    IR.ft(['ph1','ph2'])
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
    fl.next('1D diagnostic IR')
    fl.plot(select_pathway(d,signal_pathway))
    plt.axvline(x=frq_slice[0])
    plt.axvline(x=frq_slice[-1])
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
    s.ift('t2')
    s.ift(['ph1'])
    t_start = Ep_t_range[-1]/4
    t_start *= 3
    rx_offset_corr = s['t2':(t_start,None)]
    rx_offset_corr = rx_offset_corr.data.mean()
    s -= rx_offset_corr
    s.rename('indirect','time')
    s.ft('t2')
    s.ft(['ph1'])
    zero_crossing = abs(select_pathway(s['t2':Ep_f_slice],Ep_signal_pathway)).C.sum('t2').argmin('time',raw_index=True).item()
    s = s['t2':Ep_f_slice]
    if 'nScans' in s.dimlabels:
        s.mean('nScans')
    s.ift('t2')
    #}}}
    #{{{phasing
    s.ft('t2')
    s.ift('t2')
    best_shift = hermitian_function_test(select_pathway(s.C.mean('time'),
        Ep_signal_pathway),aliasing_slop=0)
    best_shift = 0.0035 #this data is bad so I have to hard code the shift
    s.setaxis('t2',lambda x: x-best_shift).register_axis({'t2':0})
    s.ft('t2')
    s.ift('t2')
    s /= zeroth_order_ph(select_pathway(s,Ep_signal_pathway))
    s.ft('t2')    
    #}}}
    #{{{Alignment
    s.ift(['ph1'])
    opt_shift,sigma, my_mask = correl_align(s.C,
            indirect_dim='time',
            signal_pathway=Ep_signal_pathway)
    s.ift('t2')
    s *= np.exp(-1j*2*pi*opt_shift*s.fromaxis('t2'))
    s.ft('t2')
    s.ift('t2')
    s.ft(['ph1'])
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
    fl.next('1D diagnostic Ep')
    fl.plot(select_pathway(d,Ep_signal_pathway))
    plt.axvline(x=frq_slice[0])
    plt.axvline(x=frq_slice[-1])
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
    fl.show();quit()
    #}}}
#{{{Relaxation rates and making Flinear
T1p = nddata(T1_list,[-1],['power'])
T1_powers=[]
print(T1p)
print(power_list)
for j in range(len(power_list)):
    if j == 0:
        T1_powers.append(power_list[j])
    else:    
        T1_powers.append(power_list[j].data)
T1p.setaxis('power',T1_powers)
T1p.set_error('power',nddata_p_vs_t.get_error())
T1p['power',0] = 0.29
print(T1p)
quit()
fl.next(r'$T_{1}$(p) vs power')
fl.plot(T1p.data,'o')
R1p=T1p.C**-1
Flinear = ((R1p - R1p['power':0.001]+R1w)**-1)
polyorder = 1
coeff = abs(Flinear).polyfit('power',order=polyorder)
power = nddata(np.linspace(0,R1p.getaxis('power')[-1],nPowers),'power')
Flinear_fine = 0
for j in range(polyorder + 1):
    Flinear_fine += coeff[j] * power **j
fl.next('Flinear',legend=True)
Flinear.set_units('power',s_int.get_units('power'))
fl.plot(Flinear,'o',label='Flinear')
Flinear_fine.set_units('power',s_int.get_units('power'))
fl.plot(Flinear_fine,label='Flinear_fine')
plt.title('polynomial fit of linear equation')
plt.ylabel("$F_{linear}$")
fl.next('R1p vs power')
R1p_fine = ((Flinear_fine)**-1) +R1p['power':0.001]-R1w
fl.plot(R1p,'x')
R1p_fine.set_units('power',R1p.get_units('power'))
fl.plot(R1p_fine)
plt.title("relaxation rates")
plt.ylabel("$R_{1}(p)$")
#}}}
#{{{ plotting with correction for heating
ksigs_T = (ppt/C)*(1-enhancement['power',:-3])*(R1p_fine)
fl.next('ksig_smax for %s'%filename)
x = enhancement['power',:-3].fromaxis('power')
fitting_line = fitdata(ksigs_T)
k,p_half,power = symbols("k, p_half, power",real=True)
ksigs_functional_form = (k*power)/(p_half+power)
fitting_line.functional_form = ksigs_functional_form
fitting_line.fit()
fl.plot(ksigs_T,'o',label='with heating correction')
fl.plot(fitting_line.eval(100),label='fit')
plt.text(0.75,0.25,fitting_line.latex(), transform=plt.gca().transAxes,size='large',
        horizontalalignment='center',color='k')
plt.title('ksigmas(p) vs Power')
plt.ylabel('ksigmas(p)')
fl.show();quit()

