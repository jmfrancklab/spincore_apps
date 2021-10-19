from pylab import *
from pyspecdata import *
from pyspecProcScripts import *
from pyspecProcScripts import lookup_table
#from scipy.optimize import leastsq,minimize,basinhopping
from sympy import symbols
fl = fl_mod()
t2 = symbols('t2')
filter_bandwidth = 20e3
gamma_eff = (14.897706/3506.5)#(14.893851/3505.6) # MHz / G
f_dip = 9.8216745#9.82103 # GHz
for thisfile,exp_type,nodename,postproc,label_str,freq_slice,field_slice in [
        ('211019_150uM_TEMPO_cap_probe_field_dep1','ODNP_NMR_comp/field_dependent',
            'field_sweep_1','field_sweep_v1',
            'TEMPO field sweep',(-1e3,1e3),(-400,250)),
        ]:
    s = find_file(thisfile,exp_type=exp_type,expno=nodename)#,
            #postproc=postproc,lookup=lookup_table)
    nPoints = s.get_prop('acq_params')['nPoints']
    nEchoes = s.get_prop('acq_params')['nEchoes']
    SW_kHz = s.get_prop('acq_params')['SW_kHz']
    nScans = s.get_prop('acq_params')['nScans']
    s.reorder('t',first=True)
    s.chunk('t',['ph1','t2'],[4,-1])
    s.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    s.reorder('t2',first=False)
    t2_max = s.getaxis('t2')[-1]
    rx_offset_corr = s['t2':(t2_max*0.75,None)]
    rx_offset_corr = rx_offset_corr.data.mean()
    s -= rx_offset_corr
    s.ft(['ph1'])
    fl.next('raw data -- coherence channels')
    s.reorder(['ph1','Field','power','t2'])
    fl.image(s)
    s.ft('t2',shift=True)
    fl.next('frequency domain raw data')
    fl.image(s)
    freqs = s.get_prop('acq_params')['mw_freqs']
    s = s['t2':freq_slice]
    s=s['ph1',1]['power',0]['nScans',0].C
    s.ift('t2')
    s.ft('t2')
    s = s['t2':(-filter_bandwidth/2,filter_bandwidth/2)]
    s.ift('t2')
    rough_center = abs(s).C.convolve('t2',0.0001).mean_all_but('t2').argmax('t2').item()
    s.setaxis(t2-rough_center)
    s.ft('t2')
    fl.next('line plots')
    for z in range(len(s.getaxis('Field'))):
        fl.plot(abs(s['Field',z]),label='%d'%z)
    s_ = s['t2':field_slice].sum('t2')
    fl.next('sweep, without hermitian')
    fl.plot(abs(s_),'o-')
    field_idx = (abs(s_.data)).argmax()
    fitting = abs(s_).polyfit('Field',order=2)
    Field = nddata(r_[3502:3508:100j],'Field')
    fl.plot(Field.eval_poly(fitting,'Field'),label='fit')
    print("ESR frequency is %f"%(freqs[0]/1e9))
    print('I found a max of the fit at',Field.eval_poly(fitting,'Field').argmax().item())
    print('I found data max at', abs(s_).argmax().item())
fl.show()
