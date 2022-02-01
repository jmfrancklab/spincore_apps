"""
Field Sweep at set power
========================

Runs a field sweep of 5-8 points around the 
estimated field for the electron resonance at the
highest power one plans to run the combined DNP
at. 
"""
import numpy as np
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
#{{{ Verify arguments compatible with board
def verifyParams():
    if (nPoints > 16*1024 or nPoints < 1):
        print("ERROR: MAXIMUM NUMBER OF POINTS IS 16384.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED NUMBER OF POINTS.")
    if (nScans < 1):
        print("ERROR: THERE MUST BE AT LEAST 1 SCAN.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED NUMBER OF SCANS.")
    if (p90 < 0.065):
        print("ERROR: PULSE TIME TOO SMALL.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED PULSE TIME.")
    if (tau_us < 0.065):
        print("ERROR: DELAY TIME TOO SMALL.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED DELAY TIME.")
    return
#}}}

mw_freqs = []

field_axis = psp.r_[3504:3509:.5]
print("Here is my field axis:",field_axis)

# Parameters for Bridge12
powers = psp.r_[3.98]
min_dBm_step = 0.5
for x in range(len(powers)):
    dB_settings = round(10*(np.log10(powers[x])+3.0)/min_dBm_step)*min_dBm_step # round to nearest min_dBm_step
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
input("Look ok?")
powers = 1e-3*10**(dB_settings/10.)
#}}}

output_name = '150mM_TEMPOL_field_dep_final'
adcOffset = 24
gamma_eff = (14.904151/3507.52)
#{{{ acq params
tx_phases = psp.r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
nScans = 1
nEchoes = 1
coherence_pathway = [('ph1',1)]
date = datetime.now().strftime('%y%m%d')
nPhaseSteps = 4
#{{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
#}}}
p90 = 4.464
deadtime = 10.0
repetition = 0.5e6

SW_kHz = 3.9
acq_ms = 1024.
nPoints = int(acq_ms*SW_kHz+0.5)
# rounding may need to be power of 2
tau_adjust_us = 0
deblank_us = 1.0
tau_us = 3500.
pad_us = 0
#}}}
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
with power_control() as p:
    dip_f=p.dip_lock(9.81,9.83)
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
        sweep_data = run_spin_echo(nScans = nScans, indirect_idx = 0, 
                indirect_len = len(field_axis), adcOffset = adcOffset,
                carrierFreq_MHz = carrierFreq_MHz, nPoints = nPoints,
                nEchoes = nEchoes, p90_us = p90, repetition = repetition,
                tau_us = tau_us, SW_kHz=SW_kHz, output_name = output_name, 
                indirect_dim1 = 'Field', indirect_dim2 = 'carrierFreq',
                ret_data = None)
        myfreqs_fields = sweep_data.getaxis('indirect')
        myfreqs_fields[0]['Field'] = first_B0
        myfreqs_fields[0]['carrierFreq'] = carrierFreq_MHz
        for B0_index,desired_B0 in enumerate(field_axis[1:]):
                true_B0 = x_server.set_field(desired_B0)
                print("My field in G is %f"%true_B0)
                time.sleep(3.0)
                new_carrierFreq_MHz = gamma_eff*true_B0
                myfreqs_fields[B0_index]['Field'] = true_B0
                myfreqs_fields[B0_index]['carrierFreq'] = new_carrierFreq_MHz
                print("My frequency in MHz is",new_carrierFreq_MHz)
                sweep_data = run_spin_echo(nScans = nScans, indirect_idx = B0_index+1,
                        indirect_len = len(field_axis), adcOffset = adcOffset,
                        carrierFreq_MHz = new_carrierFreq_MHz, nPoints = nPoints,
                        nEchoes = nEchoes, p90_us = p90, repetition = repetition,
                        tau_us = tau_us, SW_kHz=SW_kHz, output_name = output_name, 
                        indirect_dim1 = 'Field', indirect_dim2 = 'carrierFreq',
                        ret_data = sweep_data)
        SpinCore_pp.stopBoard()
acq_params = {j:eval(j) for j in dir() if j in ['tx_phases', 'carrierFreq_MHz','amplitude','nScans','nEchoes','p90','deadtime','repetition','SW_kHz','mw_freqs','nPoints','tau_adjust_us','deblank_us','tau_us','nPhaseSteps']}
sweep_data.set_prop('acq_params',acq_params)
sweep_data.name('Field_sweep')
#}}}        
myfilename = date+'_'+output_name+'.h5'
save_file = True
while save_file:
    try:
        print("SAVING FILE IN TARGET DIRECTORY...")
        sweep_data.name('field_sweep')
        sweep_data.hdf5_write(myfilename,
                directory=getDATADIR(exp_type='ODNP_NMR_comp/field_dependent'))
        print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
        print(("Name of saved data",data.name()))
        print(("Units of saved data",data.get_units('t')))
        print(("Shape of saved data",ndshape(data)))
        save_file = False
    except Exception as e:
        print(e)
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        output_name = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(output_name) is not 0:
            sweep_data.name('field_sweep')
            sweep_data.hdf5_write(date+'_'+output_name+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
fl.show();quit()
