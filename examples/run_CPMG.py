from pylab import *
from pyspecdata import *
from numpy import *
import SpinCore_pp 
from datetime import datetime
fl = figlist_var()
#{{{importing acquisition parameters
config_dict = SpinCore_pp.configuration('active.ini')
nPoints = int(config_dict['acq_time_ms']*config_dict['SW_kHz']+0.5)
#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config_dict['type'] = 'CPMG'
config_dict['date'] = f'{date}'
config_dict['cpmg_counter'] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
#}}}
#{{{better tau
marker = 1.0
tau_extra = 1000.0 # us, must be more than deadtime and more than deblank
pad_start = tau_extra - config_dict['deadtime_us']
pad_end = tau_extra - config_dict['deblank_us']*2 # marker + deblank
twice_tau = config_dict['deblank_us'] + 2*p90_us + config_dict['deadtime_us'] + pad_start + config_dict['acq_time_ms']*1e3 + pad_end + marker
tau_us = twice_tau/2.0
config_dict['tau_us'] = tau_us
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
        nScans = config_dict['nScans'],
        indirect_idx = 0,
        ph1_cyc = ph1_cyc,
        adcOffset = config_dict['adc_offset'],
        carrierFreq_MHz = config_dict['carrierFreq_MHz'],
        nPoints = nPoints,
        nEchoes = config_dict['nEchoes'],
        p90_us = config_dict['p90_us'],
        repetition = config_dict['repetition_us'],
        tau_us = config_dict['tau_us'],
        SW_kHz = config_dict['SW_kHz'],
        pad_start_us = pad_start,
        pad_end_us = pad_end,
        output_name = filename,
        ret_data = None)
#}}}
#{{{saving with acq params
SpinCore_pp.stopBoard();
data.set_prop("acq_params",config_dict.asdict())
data.name(config_dict['type']+'_'+config_dict['cpmg_counter'])
target_directory = getDATADIR(exp_type='ODNP_NMR_comp/CPMG')
filename_out = filename + '.h5'
nodename = data.name()
if phase_cycling:
    data.chunk("t",['ph1','t2'],[len(ph1_cyc),-1])
    data.setaxis('ph1', ph1_cyc/4)
    if config_dict['nScans'] > 1:
        data.setaxis('nScans',r_[0:config_dict['nScans']])
if os.path.exists(filename+'.h5'):
    print('this file already exists so we will add a node to it!')
    with h5py.File(os.path.normpath(os.path.join(target_directory,
        f"{filename_out}"))) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp")
            data.name('temp')
            nodename = 'temp'
    data.hdf5_write(f'{filename_out}/{nodename}', directory = target_directory)
else:
    data.hdf5_write(filename+'.h5',
            directory=target_directory)
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
