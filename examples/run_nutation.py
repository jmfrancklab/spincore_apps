from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
import socket
import sys
import time
from datetime import datetime
fl = figlist_var()
#{{{ Edit here to set the actual field
set_field = False
if set_field:
    B0 = 3497 # Determine this from Field Sweep
    thisB0 = xepr().set_field(B0)
#}}}
date = datetime.now().strftime('%y%m%d')
output_name = 'TEMPOL_capProbe'
adcOffset = 25
carrierFreq_MHz = 14.896101
nScans = 1
nEchoes = 1
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0,1,2,3]
    ph2_cyc = r_[0,2]
    nPhaseSteps = 8
if not phase_cycling:
    ph1_cyc = r_[0]
    ph2_cyc = r_[0]
    nPhaseSteps = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
repetition_us = 12e6
SW_kHz = 24.0
nPoints = 1024
acq_time_ms = nPoints/SW_kHz # ms
tau_us = 3500
print("ACQUISITION TIME:",acq_time,"ms")
print("TAU DELAY:",tau,"us")
data_length = 2*nPoints*nEchoes*nPhaseSteps
p90_range_us = linspace(1.,15.,40,endpoint=False)
for index,val in enumerate(p90_range_us):
    p90_us = val # us
    print("***")
    print("INDEX %d - 90 TIME %f"%(index,val))
    print("***")
    nutation_data = run_spin_echo(
            nScans = nScans,
            indirect_idx = len(p90_range_us),
            adcOffset=adcOffset,
            carrierFreq_MHz = carrierFreq_MHz,
            nPoints = nPoints,
            nEchoes = nEchoes,
            p90_us = p90_us,
            repetition = repetition_us,
            tau_us = tau_us,
            SW_kHz = SW_kHz,
            output_name = output_name,
            ret_data = None)
SpinCore_pp.stopBoard();
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
nutation_data.set_prop('acq_params',acq_params)
print("EXITING...\n")
print("\n*** *** ***\n")
save_file = True
while save_file:
    try:
        nutation_data.name('nutation')
        nutation_data.hdf5_write(date+'_'+output_name+'.h5',
                directory=getDATADIR(exp_type='ODNP_NMR_comp/nutation'))
        print("Name of saved data",nutation_data.name())
        print("Units of saved data",nutation_data.get_units('t'))
        print("Shape of saved data",ndshape(nutation_data))
        save_file = False
    except Exception as e:
        print("\nEXCEPTION ERROR.")
        print("FILE MAY ALREADY EXIST IN TARGET DIRECTORY.")
        print("WILL TRY CURRENT DIRECTORY LOCATION...")
        output_name = input("ENTER NEW NAME FOR FILE (AT LEAST TWO CHARACTERS):")
        if len(output_name) is not 0:
            nutation_data.hdf5_write(date+'_'+output_name+'.h5')
            print("\n*** FILE SAVED WITH NEW NAME IN CURRENT DIRECTORY ***\n")
            break
        else:
            print("\n*** *** ***")
            print("UNACCEPTABLE NAME. EXITING WITHOUT SAVING DATA.")
            print("*** *** ***\n")
            break
        save_file = False
fl.next('raw data')
fl.image(nutation_data)
nutation_data.ft('t',shift=True)
fl.next('FT raw data')
fl.image(nutation_data)
fl.show()

