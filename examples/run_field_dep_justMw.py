''' Field Sweep at constant power
=================================
Here we will perform a series of echoes at a range of designated field values. This is normally run at a power of 3-4 W. To run this experiment, please open Xepr on the EPR computer, connect to spectrometer, enable XEPR_API. Then, in a separate terminal, run the program XEPR_API_server.py, wait for it to tell you 'I am listening' - then, you should be able to run this program in sync with the power_control_server.
To run this in sync with the power_control_server, open a separate terminal on the NMR computer and move into git/inst_notebooks/Instruments and run winpty power_control_server(). This will print out "I am listening" when it is ready to go. You can then proceed to run this script to collect your field sweep data
'''

from pylab import *
from pyspecdata import *
import os
import sys
import SpinCore_pp
from SpinCore_pp/ppg import run_spin_echo
from datetime import datetime
import numpy as np
from Instruments import Bridge12,prologix_connection,gigatronics
from serial import Serial
from Instruments.XEPR_eth import xepr
import h5py
fl = figlist_var()
mw_freqs = []
#{{{these parameters change for each sample
field_axis = r_[3422:3426:.5]
print("Here is my field axis:",field_axis)
output_name = 'TEMPOL_heat_exch_289uM_field_dep'
node_name = 'field_sweep_1'
adcOffset = 28
gamma_eff = (14.549013/3424.42)
nScans = 1
nEchoes = 1
phase_cycling = True
coherence_pathway = [('ph1',1)]
date = datetime.now().strftime('%y%m%d')
if phase_cycling:
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
p90 = 1.781
repetition = 12e6
SW_kHz = 10
acq_ms = 200.
nPoints = int(acq_ms*SW_kHz+0.5)
tau = 3500
#}}}
#{{{check for file
myfilename = date + '_'+output_name+'.h5'
if os.path.exists(myfilename):
    raise ValueError(
            "the file %s already exists, change your output name!"%myfilename)
#}}}    
#{{{ Parameters for Bridge12
powers = r_[3.98]
min_dBm_step = 0.5
for x in range(len(powers)):
    print(powers)
    dB_settings = round(10*(log10(powers[x])+3.0)/min_dBm_step)*min_dBm_step # round to nearest min_dBm_step
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
input("Look ok?")
powers = 1e-3*10**(dB_settings/10.)
uw_dip_center_GHz = 9.82
uw_dip_width_GHz = 0.02
#}}}
#{{{run field sweep
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
with power_control() as p:
    dip_f = p.dip_lock(uw_dip_center_GHz - us_dip_width_GHz/2,
            uw_dip_center_GHz + us_dip_width_GHz/2)
    mw_freqs.append(dip_f)
    p.set_power9dB_settings)
    this_dB = dBsettings
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
                nScans = nScans,
                indirect_idx = 0,
                indirect_len = len(field_axis),
                adcOffset = adcOffset,
                carrierFreq_MHz = carrierFreq_MHz,
                nPoints=nPoints,
                nEchoes = nEchoes,
                p90_us = p90_us,
                repetition = repetition_us,
                tau_us = tau_us,
                SW_kHz = SW_kHz,
                output_name = output_name,
                indirect_fields = ('Field','carrierFreq'),
                ret_data = None)
        myfreqs_fields = sweep_data.getaxis('indirect')
        myfreqs_fields[0]['Field'] = first_B0
        myfreqs_fields[0]['carrierFreq'] = carrierFreq_MHz
        for B0_index, desired_B0 in enumerate(field_axis[1:]):
            true_B0 = x_server.set_field(desired_B0)
            logging.info("My field in G is %f"%true_B0)
            time.sleep(3.0)
            new_carrierFreq_MHz = gamma_eff*true_Bo
            myfreqs_fields[B0_index+1]['Field'] = true_B0
            myfreqs_fields[B0_index+1]['carrierFreq'] = new_carrierFreq_MHz
            logging.info("My frequency in MHz is", new_carrierFreq_MHz)
            run_spin_echo(
                    nScans=nScans,
                    indirect_idx = B0_index+1,
                    indirect_len = len(field_axis),
                    adcOffset = adcOffset,
                    carrierFreq_MHz=carrierFreq_MHz,
                    nPoints=nPoints,
                    nEchoes = nEchoes,
                    p90_us = p90_us,
                    repetition = repetition_us,
                    tau_us = tau_us,
                    SW_kHz=SW_kHz,
                    output_name = output_name,
                    ret_data = sweep_data)
        SpinCore_pp.stopBoard()
acq_params = {j:eval(j) for j in dir() if j in [
    'tx_phases',
    'carrierFreq_MHz', 
    'amplitude', 
    'nScans',
    'nEchoes',
    'p90',
    'deadtime',
    'repetition',
    'SW_kHz',
    'mw_freqs',
    'nPoints',
    'tau_adjust_us',
    'deblank_us',
    'tau_us',
    'nPhaseSteps']}
sweep_data.set_prop('acq_params',acq_params)
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

