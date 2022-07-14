import configparser
from pylab import *
from pyspecdata import *
from numpy import *
import SpinCore_pp 
from datetime import datetime
fl = figlist_var()

#{{{importing acquisition parameters
values, config = SpinCore_pp.parser_function('active.ini')
nPoints = int(values['acq_time_ms']*values['SW_kHz']+0.5)
#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config.set('file_names','type','CPMG')
config.set('file_names','date',f'{date}')
values['cpmg_counter'] += 1
config.set('file_names','echo_counter',str(values['echo_counter']))
config.write(open('active.ini','w')) #write edits to config file
values, config = SpinCore_pp.parser_function('active.ini') #translate changes in config file to our dict
filename = f"{values['date']}_{values['chemical']}_{values['type']}{values['cpmg_counter']}"
#}}}
#{{{better tau
marker = 1.0
tau_extra = 1000.0 # us, must be more than deadtime and more than deblank
pad_start = tau_extra - values['deadtime_us']
pad_end = tau_extra - values['deblank_us']*2 # marker + deblank
twice_tau = values['deblank_us'] + 2*p90_us + values['deadtime_us'] + pad_start + values['acq_time_ms']*1e3 + pad_end + marker
tau_us = twice_tau/2.0
#}}}
#{{{phase cycling
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 4
    ph1_cyc = r_[0, 1, 2, 3]
if not phase_cycling:
    nPhaseSteps = 1
#}}}   
#{{{run cpmg
# NOTE: Number of segments is nEchoes * nPhaseSteps
data = run_cpmg(
        nScans = values['nScans'],
        indirect_idx = 0,
        ph1_cyc = ph1_cyc,
        adcOffset = values['adc_offset'],
        carrierFreq_MHz = values['carrierFreq_MHz'],
        nPoints = nPoints,
        nEchoes = values['nEchoes'],
        p90_us = values['p90_us'],
        repetition = values['repetition_us'],
        tau_us = tau_us,
        SW_kHz = values['SW_kHz'],
        pad_start_us = pad_start,
        pad_end_us = pad_end,
        output_name = filename,
        ret_data = None)
#}}}
#{{{saving with acq params
data.set_prop("acq_params",values)
data.name(values['type'])
if phase_cycling:
    data.chunk("t",['ph1','t2'],[len(ph1_cyc),-1])
    data.setaxis('ph1', ph1_cyc/4)
data.hdf5_write(myfilename,
        directory=getDATADIR(exp_type = 'ODNP_NMR_comp/CPMG'))
SpinCore_pp.stopBoard();
#}}}
#{{{visualize raw data
s = data.C
s.set_units('t','s')
orig_t = s.getaxis('t')
acq_time_s = orig_t[nPoints]
fl.next('time')
fl.plot(abs(s))
fl.plot(s.real,alpha=0.4)
fl.plot(s.imag,alpha=0.4)
s.ft('t',shift=True)
fl.next('freq')
fl.plot(abs(s))
fl.plot(s.real,alpha=0.4)
fl.plot(s.imag,alpha=0.4)
fl.show()
#}}}
