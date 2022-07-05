"""
Spin Echo
=========

To run this experiment, please open Xepr on the EPR computer, connect to
spectrometer, load the experiemnt 'set_field' and enable XEPR API. Then, in a
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
import sys
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
import numpy as np
from Instruments.XEPR_eth import xepr
fl = figlist_var()
config = configparser.ConfigParser()
config.sections()
config.read('active.ini')
#{{{importing acquisition parameters
acq_params = config['acq_params']
p90_us = float(acq_params['p90_us'])
deadtime_us = float(acq_params['deadtime_us'])
adcOffset = float(acq_params['adc_offset'])
amplitude = float(acq_params['amplitude'])
deblank_us = float(acq_params['deblank_us'])
tau_us = float(acq_params['tau_us'])
repetition_us = float(acq_params['repetition_us'])
nScans = float(acq_params['nScans'])
SW_kHz = float(acq_params['sw_khz'])
acq_ms = float(acq_params['acq_time_ms'])
nPoints = int(acq_ms*SW_kHz+0.5)
#{{{create filename and save to config file
output_name = 'test'
node_name = 'echo'
date = datetime.now().strftime('%y%m%d')
file_names = config['file_names']
config.set('file_names','date',f'{date}')
config.set('file_names','chemical',output_name)
config.set('file_names','type',node_name)
filename = file_names['date']+'_'+file_names['chemical']+'_'+file_names['type']
#}}}
#}}}
user_sets_Freq = True
user_sets_Field = True
#{{{ set field here
if user_sets_Field:
    # You must enter field set on XEPR here
    true_B0 = 3424.42
    print("My field in G should be %f"%true_B0)
#}}}
#{{{let computer set field
if not user_sets_Field:
    desired_B0 = 3506.50
    with xepr() as x:
        true_B0 = x.set_field(desired_B0)
    print("My field in G is %f"%true_B0)
#}}}
#{{{ set frequency here
if user_sets_Freq:
    carrierFreq_MHz = 14.8978438
    config.set('acq_params','carrierFreq_MHz',carrierFreq_MHz)
    print("My frequency in MHz is",carrierFreq_MHz)
#}}}
#{{{ let computer set frequency
if not user_sets_Freq:
    gamma_eff = (14.897706/3506.5)
    carrierFreq_MHz = gamma_eff*true_B0
    config.set('acq_params','carrierFreq_MHz',carrierFreq_MHz)
    print("My frequency in MHz is",carrierFreq_MHz)
#}}}
tx_phases = r_[0.0,90.0,180.0,270.0]
nEchoes = 1
phase_cycling = True
coherence_pathway = [('ph1',1)]
if phase_cycling:
    ph1_cyc = r_[0,1,2,3]
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
#{{{ check for file
myfilename = date + "_" + output_name + ".h5"
if os.path.exists(myfilename):
    raise ValueError(
            "the file %s already exists, change your output name!"%myfilename
            )
#}}}
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
data_length = 2*nPoints*nEchoes*nPhaseSteps
echo_data = run_spin_echo(
        nScans=nScans,
        indirect_idx = 0,
        indirect_len = 1,
        ph1_cyc = ph1_cyc,
        adcOffset = adcOffset,
        carrierFreq_MHz = carrierFreq_MHz,
        nPoints = nPoints,
        nEchoes = nEchoes,
        p90_us = p90_us,
        repetition = repetition_us,
        tau_us = tau_us,
        SW_kHz = SW_kHz,
        output_name=output_name,
        ret_data = None)
SpinCore_pp.stopBoard()
echo_data.set_prop("postproc_type","proc_Hahn_echoph")
acq_params = {j: eval(j) for j in dir() if j in [
    "adcOffset",
    "carrierFreq_MHz",
    "amplitude",
    "nScans",
    "nEchoes",
    "p90_us",
    "deadtime_us",
    "repetition_us",
    "SW_kHz",
    "nPoints",
    "deblank_us",
    "tau_us",
    "nPhaseSteps",
    ]
    }
echo_data.set_prop("acq_params",acq_params)
echo_data.name(node_name)
if phase_cycling:
    echo_data.chunk('t',['ph1','t2'],[4,-1])
    echo_data.setaxis('ph1',r_[0.,1.,2.,3.]/4)
    if nScans > 1:
        echo_data.setaxis('nScans',r_[0:nScans])
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
echo_data.hdf5_write(filename+'.h5',
        directory=getDATADIR(exp_type='ODNP_NMR_comp/Echoes'))
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data",echo_data.name()))
print(("Shape of saved data",ndshape(echo_data)))
