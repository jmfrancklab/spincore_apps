"""
Field Sweep at set power
========================

Runs a field sweep of 5-8 points around the 
estimated field for the electron resonance at the
highest power one plans to run the combined DNP
at. 
"""
import numpy as np
from numpy import r_
import pyspecdata as psp
import os
import sys
import SpinCore_pp
import time
from Instruments import power_control,Bridge12,prologix_connection,gigatronics
from datetime import datetime
from Instruments.XEPR_eth import xepr
from pylab import *
from SpinCore_pp.ppg import run_spin_echo
fl = psp.figlist_var()
mw_freqs = []
#{{{These change for each sample
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
field_axis = psp.r_[3503:3508:.5]
logger.info(strm("Here is my field axis:",field_axis))
powers = r_[3.98]
min_dBm_step = 0.5
output_name = '150mM_TEMPOL_field_dep'
adcOffset = 25
gamma_eff = (14.904040/3507.54)
nScans = 1
p90 = 4.464
repetition = 0.5e6
SW_kHz = 3.9
acq_ms = 1024.
tau_us = 3500.
ph1_cyc = r_[0,1,2,3]
uw_dip_center_GHz = 9.82
uw_dip_width_GHz = 0.02
#}}}

#{{{ Parameters for Bridge12
for x in range(len(powers)):
    dB_settings = round(10*(np.log10(powers[x])+3.0)/min_dBm_step)*min_dBm_step # round to nearest min_dBm_step
logger.info(strm("dB_settings",dB_settings))
logger.info(strm("correspond to powers in Watts",10**(dB_settings/10.-3)))
powers = 1e-3*10**(dB_settings/10.)
#}}}
#{{{ acq params
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nEchoes = 1
date = datetime.now().strftime('%y%m%d')
nPhaseSteps = len(ph1_cyc)
deadtime = 10.0
nPoints = int(acq_ms*SW_kHz+0.5)
# rounding may need to be power of 2
tau_adjust_us = 0
deblank_us = 1.0
pad_us = 0
#}}}
total_pts = nPoints*nPhaseSteps
# {{{ check for file
myfilename = date + "_" + output_name + ".h5"
if os.path.exists(myfilename):
    raise ValueError(
        "the file %s already exists, so I'm not going to let you proceed!" % myfilename
    )
# }}}
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
with power_control() as p:
    dip_f=p.dip_lock(uw_dip_center_GHz - uw_dip_width_GHz / 2,
            uw_dip_center_GHz + uw_dip_width_GHz / 2,)
    mw_freqs.append(dip_f)
    p.set_power(dB_settings)
    this_dB = dB_settings
    for k in range(10):
        time.sleep(0.5)
        if p.get_power_setting()>= this_dB: break
    if p.get_power_setting() < this_dB: raise ValueError("After 10 tries, the power has still not settled")    
    meter_powers = np.zeros_like(dB_settings)
    with xepr() as x_server:
        first_B0 = x_server.set_field(field_axis[0])
        time.sleep(3.0)
        carrierFreq_MHz = gamma_eff*first_B0
        sweep_data = run_spin_echo(
                nScans = nScans, 
                indirect_idx = 0, 
                indirect_len = len(field_axis), 
                adcOffset = adcOffset,
                carrierFreq_MHz = carrierFreq_MHz, 
                nPoints = nPoints,
                nEchoes = nEchoes, 
                p90_us = p90, 
                repetition = repetition,
                tau_us = tau_us, 
                SW_kHz=SW_kHz, 
                output_name = output_name, 
                indirect_fields = ('Field', 'carrierFreq'),
                ret_data = None)
        myfreqs_fields = sweep_data.getaxis('indirect')
        myfreqs_fields[0]['Field'] = first_B0
        myfreqs_fields[0]['carrierFreq'] = carrierFreq_MHz
        for B0_index,desired_B0 in enumerate(field_axis[1:]):
                true_B0 = x_server.set_field(desired_B0)
                logger.info(strm("My field in G is %f"%true_B0))
                time.sleep(3.0)
                new_carrierFreq_MHz = gamma_eff*true_B0
                myfreqs_fields[B0_index+1]['Field'] = true_B0
                myfreqs_fields[B0_index+1]['carrierFreq'] = new_carrierFreq_MHz
                logger.info(strm("My frequency in MHz is",new_carrierFreq_MHz))
                run_spin_echo(
                        nScans = nScans, 
                        indirect_idx = B0_index+1,
                        indirect_len = len(field_axis), 
                        adcOffset = adcOffset,
                        carrierFreq_MHz = new_carrierFreq_MHz, 
                        nPoints = nPoints,
                        nEchoes = nEchoes, 
                        p90_us = p90, 
                        repetition = repetition,
                        tau_us = tau_us, 
                        SW_kHz=SW_kHz, 
                        output_name = output_name, 
                        ret_data = sweep_data)
        SpinCore_pp.stopBoard()
acq_params = {
        j:eval(j) 
        for j in dir() 
        if j 
        in [
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
            'nPhaseSteps'
            ]
        }
sweep_data.set_prop('acq_params',acq_params)
sweep_data.name('Field_sweep')
#}}}        
myfilename = date+'_'+output_name+'.h5'
sweep_data.hdf5_write(myfilename,directory=getDATADIR(exp_type='ODNP_NMR_comp/field_dependent'))
logger.debug(strm(("Name of saved data",data.name()))
logger.debug(strm("Shape of saved data",ndshape(data)))
fl.show();quit()

