#{{{ note on phase cycling
'''
FOR PHASE CYCLING: Provide both a phase cycle label (e.g.,
'ph1', 'ph2') as str and an array containing the indices
(i.e., registers) of the phases you which to use that are
specified in the numpy array 'tx_phases'.  Note that
specifying the same phase cycle label will loop the
corresponding phase steps together, regardless of whether
the indices are the same or not.
    e.g.,
    The following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph1',r_[2,3]),
    will provide two transients with phases of the two pulses (p1,p2):
        (0,2)
        (1,3)
    whereas the following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph2',r_[2,3]),
    will provide four transients with phases of the two pulses (p1,p2):
        (0,2)
        (0,3)
        (1,2)
        (1,3)
FURTHER: The total number of transients that will be
collected are determined by both nScans (determined when
calling the appropriate marker) and the number of steps
calculated in the phase cycle as shown above.  Thus for
nScans = 1, the SpinCore will trigger 2 times in the first
case and 4 times in the second case.  for nScans = 2, the
SpinCore will trigger 4 times in the first case and 8 times
in the second case.
'''
#}}}
from pyspecdata import *
from numpy import *
from datetime import datetime
from . import SpinCore_pp 
from config_parser_fn import parser_function
fl = figlist_var()
#{{{importing acquisition parameters
values, config = parser_function('active.ini')
nPoints = int(values['acq_time_ms']*values['SW_kHz']+0.5)
#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config.set('file_names','type','CPMG_calib')
config.set('file_names','date',f'{date}')
echo_counter = values['echo_counter'])
echo_counter += 1
config.set('file_names','echo_counter',str(echo_counter))
config.write(open('active.ini','w')) #write edits to config file
values, config = parser_function('active.ini') #translate changes in config file to our dict
filename = str(values['date']) + '_' + values['chemical'] + '_' + values['type'] + '_' + str(values['echo_counter'])
#}}}

marker = 1.0

tau_extra = 200.0 # us, must be more than deadtime and more than deblank
pad_start = tau_extra - values['deadtime_us']
pad_end = tau_extra - values['deblank_us']*2 

nPhaseSteps = 2
ph1_cyc = r_[0,2]
p90_range = linspace(3.0,4.0,5)#,endpoint=False)
# NOTE: Number of segments is nEchoes * nPhaseSteps
for index,val in enumerate(p90_range):
    p90 = val # us
    twice_tau = values['deblank_us'] + 2*values['p90_us'] + values['deadtime_us'] + pad_start + values['acq_time_ms']*1e3 + pad_end + marker
    tau_us = twice_tau/2.0
    print("***")
    print("INDEX %d - 90 TIME %f"%(index,val))
    print("***")
    if index == 0:
        nutation_data = run_cpmg(
                nScans=values['nScans'],
                indirect_idx = 0,
                indirect_len = len(p90_range)+1,
                adcOffset = values['adc_offset'],
                carrierFreq_MHz=values['carrierFreq_MHz'],
                nPoints=nPoints,
                nEchoes = values['nEchoes'],
                p90_us = values['p90_us'],
                repetition_us = values['repetition_us'],
                pad_start_us = pad_start,
                pad_end_us = pad_end,
                tau_us = values['tau_us'],
                SW_kHz=values['SW_kHz'],
                output_name=filename,
                ph1_cyc = ph1_cyc,
                ret_data = None)
    else:
         run_cpmg(
                nScans=values['nScans'],
                indirect_idx = index+1,
                indirect_len = len(p90_range+1),
                adcOffset = values['adc_offset'],
                carrierFreq_MHz = values['carrierFreq_MHz'],
                nPoints=nPoints,
                nEchoes = values['nEchoes'],
                p90_us = vlaues['p90_us'],
                repetition_us = values['repetition_us'],
                pad_start_us = pad_start,
                pad_end_us = pad_end,
                tau_us = values['tau_us'],
                SW_kHz=values['SW_kHz'],
                output_name=filename,
                ph1_cyc = ph1_cyc,
                ret_data = nutation_data)
nutation_data.set_prop("acq_params",values)
nutation_data.name(values['type'])
nutation_data.chunk('t',['ph1','t2'],[len(ph1_cyc),-1])
nutation_data.setaxis('ph1',ph1_cyc/4)
nutation_data.hdf5_write(myfilename)
SpinCore_pp.stopBoard();
fl.next('raw data')
fl.image(nutation_data)
nutation_data.ft('t',shift=True)
fl.next('FT raw data')
fl.image(nutation_data)
fl.show()
