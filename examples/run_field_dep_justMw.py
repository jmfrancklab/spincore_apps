''' Field Sweep at constant power
=================================
Here we will perform a series of echoes at a range of designated field values. This is normally run at a power of 3-4 W. To run this experiment, please open Xepr on the EPR computer, connect to spectrometer, enable XEPR_API. Then, in a separate terminal, run the program XEPR_API_server.py, wait for it to tell you 'I am listening' - then, you should be able to run this program in sync with the power_control_server.
To run this in sync with the power_control_server, open a separate terminal on the NMR computer and move into git/inst_notebooks/Instruments and run winpty power_control_server(). This will print out "I am listening" when it is ready to go. You can then proceed to run this script to collect your field sweep data
'''

from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp/ppg import run_spin_echo
from datetime import datetime
import numpy as np
from Instruments.XEPR_eth import xepr
import h5py
fl = figlist_var()
mw_freqs = []
field_axis = r_[3422:3426:.5]
#{{{importing acquisition parameters
values, config = parser_function('active.ini')
#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config.set('file_names','type','echo')
config.set('file_names','date',f'{date}')
echo_counter = values['echo_counter'])
echo_counter += 1
config.set('file_names','echo_counter',str(echo_counter))
config.write(open('active.ini','w')) #write edits to config file
values, config = parser_function('active.ini') #translate changes in config file to our dict
filename = values['date']+'_'+values['chemical']+'_'+values['type']+'_'+values['echo_counter']
gamma_eff = (values['carrierFreq_MHz']/values['Field'])
#}}}
#{{{phase cycling
print("Here is my field axis:",field_axis)
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
nPoints = int(values['acq_time_ms']*values['SW_kHz']+0.5)
#}}}
#{{{check for file
if os.path.exists(myfilename):
    raise ValueError(
            "the file %s already exists, change your output name!"%myfilename)
#}}}    
#{{{ Parameters for Bridge12
powers = values['max_power']
min_dBm_step = 0.5
for x in range(len(powers)):
    dB_settings = round(10*(log10(powers[x])+3.0)/min_dBm_step)*min_dBm_step # round to nearest min_dBm_step
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
input("Look ok?")
powers = 1e-3*10**(dB_settings/10.)
#}}}
#{{{run field sweep
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
with power_control() as p:
    dip_f = p.dip_lock(values['uw_dip_center_GHz'] - values['uw_dip_width_GHz']/2,
            values['uw_dip_center_GHz'] + values['uw_dip_width_GHz']/2)
    mw_freqs.append(dip_f)
    p.set_power(dB_settings)
    this_dB = dB_settings
    for k in range(10):
        time.sleep(0.5)
        if p.get_power_setting()>= this_dB: break
    if p.get_power_setting() < this_dB: raise ValueError("After 10 tries, this power has still not settled")
    meter_powers = np.zeros_like(dB_settings)
    with xepr() as x_server:
        first_B0 = x_server.set_field(field_axis[0])
        time.sleep(3.0)
        carrierFreq_MHz = gamma_eff * first_B0
        sweep_data = run_spin_echo(
                nScans = values['nScans'],
                indirect_idx = 0,
                indirect_len = len(field_axis),
                adcOffset = values['adc_offset'],
                carrierFreq_MHz = values['carrierFreq_MHz'],
                nPoints=nPoints,
                nEchoes = values['nEchoes'],
                p90_us = values['p90_us'],
                repetition = values['repetition_us'],
                tau_us = values['tau_us'],
                SW_kHz = values['SW_kHz'],
                output_name = filename,
                indirect_fields = ('Field','carrierFreq'),
                ret_data = None)
        myfreqs_fields = sweep_data.getaxis('indirect')
        myfreqs_fields[0]['Field'] = first_B0
        myfreqs_fields[0]['carrierFreq'] = values['carrierFreq_MHz']
        for B0_index, desired_B0 in enumerate(field_axis[1:]):
            true_B0 = x_server.set_field(desired_B0)
            logging.info("My field in G is %f"%true_B0)
            time.sleep(3.0)
            new_carrierFreq_MHz = gamma_eff*true_B0
            myfreqs_fields[B0_index+1]['Field'] = true_B0
            myfreqs_fields[B0_index+1]['carrierFreq'] = new_carrierFreq_MHz
            logging.info("My frequency in MHz is", new_carrierFreq_MHz)
            run_spin_echo(
                    nScans=values['nScans'],
                    indirect_idx = B0_index+1,
                    indirect_len = len(field_axis),
                    adcOffset = values['adc_offset'],
                    carrierFreq_MHz=values['carrierFreq_MHz'],
                    nPoints=nPoints,
                    nEchoes = values['nEchoes'],
                    p90_us = values['p90_us'],
                    repetition = values['repetition_us'],
                    tau_us = values['tau_us'],
                    SW_kHz=values['SW_kHz'],
                    output_name = filename,
                    ret_data = sweep_data)
        SpinCore_pp.stopBoard()
sweep_data.set_prop('acq_params',values)
#}}}
#{{{chunk and save data
if phase_cycling:
    sweep_data.chunk("t",['ph1','t2'],[4,-1])
    sweep_data.setaxis("ph1",r_[0.0,1.0,2.0,3.0]/4)
else:
    pass
sweep_data.reorder('t2',first=False)
sweep_data.ft('t2',shift=True)
sweep_data.ft('ph1',unitary=True)
sweep_data.name('Field_sweep')
sweep_data.hdf5_write(myfilename, directory = psp.getDATADIR(exp_type='ODNP_NMR_comp/field_dependent'))

