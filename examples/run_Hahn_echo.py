'''Hahn Echo Experiment
=======================
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
'''

from pylab import *
from pyspecdata import *
import os
import sys
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
import numpy as np
from Instruments import power_control
from Instruments.XEPR_eth import xepr
import h5py
fl = figlist_var()
p90_us = 4.477
date = datetime.now().strftime('%y%m%d')
#{{{these parameters change for each sample
output_name = 'test'
node_name = 'echo'
adcOffset = 28
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
    print("My frequency in MHz is",carrierFreq_MHz)
#}}}
#{{{ let computer set frequency
if not user_sets_Freq:
    gamma_eff = (14.897706/3506.5)
    carrierFreq_MHz = gamma_eff*true_B0
    print("My frequency in MHz is",carrierFreq_MHz)
#}}}
nScans = 1
nEchoes = 1
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0,1,2,3]
    nPhaseSteps = 4
if not phase_cycling:
    ph1_cyc = r_[0]
    nPhaseSteps = 1
repetition_us = 1e6
SW_kHz = 3.9
acq_ms = 1024.
nPoints = int(acq_ms*SW_kHz+0.5)
tau_us = 3500
#}}}
#{{{check for file
myfilename = date + "_" + output_name + ".h5"
if os.path.exists(myfilename):
    raise ValueError(
            "the file %s already exists, change your output name!"%myfilename
            )
#}}}    
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
print(("ACQUISITION TIME:",acq_ms,"ms"))
print(("TAU DELAY:",tau_us,"us"))
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
        data.setaxis('nScans',r_[0:nScans])
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
echo_data.hdf5_write(date+'_'+output_name+'.h5',
        directory=getDATADIR(exp_type='ODNP_NMR_comp/Echoes'))
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data",echo_data.name()))
print(("Shape of saved data",ndshape(echo_data)))
