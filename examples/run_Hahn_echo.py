"""
Spin Echo
=========

To run this experiment, please open Xepr on the EPR computer, connect to
spectrometer, load the experiment 'set_field' and enable XEPR API. Then, in a
separate terminal, run the program XEPR_API_server.py, and wait for it to
tell you 'I am listening' - then, you should be able to run this program from
the NMR computer to set the field etc. 

Note the booleans user_sets_Freq and
user_sets_Field allow you to run experiments as previously run in this lab.
If both values are set to True, this is the way we used to run them. If both
values are set to False, you specify what field you want, and the computer
will do the rest.
"""

import configparser
from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
from Instruments.XEPR_eth import xepr
from config_parser_fn import parser_function
fl = figlist_var()
#{{{importing acquisition parameters
values, config = parser_function('active.ini')
file_names = config['file_names']
acq_params = config['acq_params']
nPoints = int(values['acq_time_ms']*values['SW_kHz']+0.5)
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
#}}}
user_sets_Freq = True
user_sets_Field = True
#{{{ set field here
if user_sets_Field:
    pass
#}}}
#{{{let computer set field
if not user_sets_Field:
    desired_B0 = values['Field']
    with xepr() as x:
        true_B0 = x.set_field(desired_B0)
    print("I set the field to %f"%true_B0)
#}}}
#{{{ set frequency here
if user_sets_Freq:
    carrierFreq_MHz = values['carrierFreq_MHz']
    print('setting frequency to:',carrierFreq_MHz)
#}}}
#{{{ let computer set frequency
if not user_sets_Freq:
    gamma_eff = values['carrierFreq_MHz']/values['Field']
    carrierFreq_MHz = gamma_eff*true_B0
    config.set('acq_params','carrierFreq_MHz',carrierFreq_MHz)
    config.write(open('active.ini','w')) #write edits to config file
    values, config = parser_function('active.ini') #translate changes in config file to our dict
    print("My frequency in MHz is",carrierFreq_MHz)
#}}}
#{{{set phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0,1,2,3]
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
#}}}    
#{{{ check for file
myfilename = filename + ".h5"
if os.path.exists(myfilename):
    raise ValueError(
            "the file %s already exists, change your output name!"%myfilename
            )
#}}}
#{{{check total points
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
#}}}
#{{{acquire echo
echo_data = run_spin_echo(
        nScans=values['nScans'],
        indirect_idx = 0,
        indirect_len = 1,
        ph1_cyc = ph1_cyc,
        adcOffset = values['adc_offset'],
        carrierFreq_MHz = carrierFreq_MHz,
        nPoints = nPoints,
        nEchoes = values['nEchoes'],
        p90_us = values['p90_us'],
        repetition = values['repetition_us'],
        tau_us = values['tau_us'],
        SW_kHz = values['SW_kHz'],
        output_name = filename,
        ret_data = None)
SpinCore_pp.stopBoard()
#}}}
#{{{setting acq_params
echo_data.set_prop("postproc_type","proc_Hahn_echoph")
echo_data.set_prop("acq_params",values)
echo_data.name(values['type'])
#}}}
#{{{Look at raw data
if phase_cycling:
    echo_data.chunk('t',['ph1','t2'],[4,-1])
    echo_data.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    if values['nScans'] > 1:
        echo_data.setaxis('nScans',r_[0:values['nScans']])
    fl.next('image')
    echo_data.mean('nScans')
    fl.image(echo_data)
    echo_data.ft('t2',shift=True)
    fl.next('image - ft')
    fl.image(echo_data)
    fl.next('image - ft, coherence')
    echo_data.ft(['ph1'])
    fl.image(echo_data)
    fl.next('data plot')
    data_slice = echo_data['ph1',1]
    fl.plot(data_slice, alpha=0.5)
    fl.plot(data_slice.imag, alpha=0.5)
    fl.plot(abs(data_slice), color='k', alpha=0.5)
else:
    fl.next('raw data')
    fl.plot(echo_data)
    echo_data.ft('t',shift=True)
    fl.next('ft')
    fl.plot(echo_data.real)
    fl.plot(echo_data.imag)
    fl.plot(abs(echo_data),color='k',alpha=0.5)
#}}}    
echo_data.hdf5_write(filename+'.h5',
        directory=getDATADIR(exp_type='ODNP_NMR_comp/Echoes'))
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data",echo_data.name()))
print(("Shape of saved data",ndshape(echo_data)))
fl.show()
