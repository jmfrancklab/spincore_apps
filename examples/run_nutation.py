from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
import socket
import sys
import time
from datetime import datetime
fl = figlist_var()
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
#{{{Parameters that change for new samples
output_name = 'TEMPOL_capillary_probe_nutation_1'
adcOffset = 39
carrierFreq_MHz = 14.896010
nScans = 1
nEchoes = 1
phase_cycling = True
repetition = 12e6
p90_range = linspace(1.,15.,40,endpoint=False)
#}}}
#{{{These should stay the same regardless of sample
date = datetime.now().strftime('%y%m%d')
ph1_cyc = r_[0,2]
ph2_cyc = r_[0,2]
# NOTE: Number of segments is nEchoes * nPhaseSteps
SW_kHz = 24.0
nPoints = 1024
acq_time = nPoints/SW_kHz # ms
tau_adjust = 0.0
tau = 3500
print("ACQUISITION TIME:",acq_times,"ms")
print("TAU DELAY:",tau,"us")
#}}}
nutation_data = spin_echo(nScans=nScans, indirect_idx = index, 
            indirect_len = len(p90_range), adcOffset = adcOffset,
            carrierFreq_MHz = carrierFreq_MHz, nPoints = nPoints,
            nEchoes=nEchoes, p90_us = p90_range[0], repetition = repetition,
            tau_us = tau, SW_kHz = SW_kHz, output_name = output_name,
            indirect_dim1 = 'p90_time', ph1_cyc = ph1_cyc, ph2_cyc = ph2_cyc,
            ret_data = None)
p90_coords = nutation_data.getaxis('indirect')
p90_coords[0]['p90_time'] = p90_range[0]
for index,val in enumerate(p90_range[1:]):
    p90 = val # us
    nutation_data = spin_echo(nScans=nScans, indirect_idx = index+1, 
            indirect_len = len(p90_range), adcOffset = adcOffset,
            carrierFreq_MHz = carrierFreq_MHz, nPoints = nPoints,
            nEchoes=nEchoes, p90_us = p90, repetition = repetition,
            tau_us = tau, SW_kHz = SW_kHz, output_name = output_name,
            indirect_dim1 = 'p90_time', ph1_cyc = ph1_cyc, ph2_cyc = ph2_cyc,
            ret_data = nutation_data)
    p90_coords[index+1]['p90_time'] = p90
acq_params = {j:eval(j) in dir() if j in ['adcOffset', 'carrierFreq_MHz', 'amplitude',
    'nScans', 'nEchoes', 'p90_range', 'deadtime', 'repetition', 'SW_kHz',
    'nPoints', 'tau_adjust', 'deblank_us', 'tau', 'nPhaseSteps']}
acq_params['pulprog'] = 'spincore_nutation_v3'
nutation_data.set_prop('acq_params',acq_params)
nutation_data.name('nutation')
myfilename = date + '_' + output_name + '.h5'
nutation_data.chunk('t',
        ['ph2','ph1','t2'],[len(ph1_cyc),len(ph2_cyc),-1]).setaxis(
                'ph2',ph2_cyc/4).setaxis('ph1',ph1_cyc/4)
nutation_data.reorder('t2',first=False)
while save_file:
    try:
        print("SAVING FILE...")
        nutation_data.hdf5_write(myfilename,
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
SpinCore_pp.stopBoard()
fl.next('raw data')
fl.image(nutation_data)
nutation_data.ft('t',shift=True)
fl.next('FT raw data')
fl.image(nutation_data)
fl.show()

