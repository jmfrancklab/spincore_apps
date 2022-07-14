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
from pylab import *
from pyspecdata import *
from numpy import *
import os
import SpinCore_pp
from Instruments import Bridge12,prologix_connection,gigatronics
from datetime import datetime
import time
import configparser
from config_parser_fn import parser_function

fl = figlist_var()
#{{{importing acquisition parameters
values, config = parser_function('active.ini')
nPoints = int(values['acq_time_ms']*values['SW_kHz']+0.5)
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
    if (tau < 0.065):
        print("ERROR: DELAY TIME TOO SMALL.")
        print("EXITING.")
        quit()
    else:
        print("VERIFIED DELAY TIME.")
    return
#}}}

#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config.set('file_names','type','signal')
config.set('file_names','date',f'{date}')
echo_counter = values['echo_counter'])
echo_counter += 1
config.set('file_names','echo_counter',str(echo_counter))
config.write(open('active.ini','w')) #write edits to config file
values, config = parser_function('active.ini') #translate changes in config file to our dict
filename = str(values['date']) + '_' + values['chemical'] + '_' + values['type'] + '_' + str(values['echo_counter'])
#}}}
#{{{power settings
dB_settings = gen_powerlist(values['max_power'],values['power_steps'])
append_dB = [dB_settings[abs(10**(dB_settings/10.-3)-values['max_power']*frac).argmin()]
        for frac in [0.75,0.5,0.25]]
dB_settings = append(dB_settings,append_dB)
print("dB_settings",dB_settings)
print("correspond to powers in Watts",10**(dB_settings/10.-3))
input("Look ok?")
powers = 1e-3*10**(dB_settings/10.)
#}}}
#{{{make better tau
marker = 1.0
tau_extra = 5000.0 # us, must be more than deadtime and more than deblank
pad_start = tau_extra - values['deadtime_us']
pad_end = tau_extra - values['deblank_us']*2 # marker + deblank
twice_tau = values['deblank_us'] + 2*values['p90_us'] + values['deadtime_us'] + pad_start + values['acq_time_ms']*1e3 + pad_end + marker
tau_us = twice_tau/2.0
#}}}
#{{{phase cycling
nPhaseSteps = 2
ph1_cyc = r_[0,2]
# NOTE: Number of segments is nEchoes * nPhaseSteps
#}}}
#{{{run CPMG
cpmg_data = run_cpmg(
        nScans = values['nScans'],
        indirect_idx = 0,
        indirect_len = len(powers) +1,
        ph1_cyc = ph1_cyc,
        adcOffset = values['adc_offset'],
        carrierFreq_MHz = values['carrierFreq_MHz'],
        nPoints=nPoints,
        nEchoes = values['nEchoes'],
        p90_us = values['p90_us'],
        repetition_us = values['repetition_us'],
        pad_start_us = pad_start,
        pad_end_us = pad_end,
        tau_us = tau_us,
        SW_kHz = values['SW_kHz'],
        output_name = filename,
        ret_data = None)
#raw_input("CONNECT AND TURN ON BRIDGE12...")
with Bridge12() as b:
    b.set_wg(True)
    b.set_rf(True)
    b.set_amp(True)
    this_return = b.lock_on_dip(ini_range=(9.815e9,9.83e9))
    dip_f = this_return[2]
    print("Frequency",dip_f)
    b.set_freq(dip_f)
    meter_powers = zeros_like(dB_settings)
    for j,this_power in enumerate(dB_settings):
        print("\n*** *** *** *** ***\n")
        print("SETTING THIS POWER",this_power,"(",dB_settings[j-1],powers[j],"W)")
        if j>0 and this_power > last_power + 3:
            last_power += 3
            print("SETTING TO...",last_power)
            b.set_power(last_power)
            time.sleep(3.0)
            while this_power > last_power+3:
                last_power += 3
                print("SETTING TO...",last_power)
                b.set_power(last_power)
                time.sleep(3.0)
            print("FINALLY - SETTING TO DESIRED POWER")
            b.set_power(this_power)
        elif j == 0:
            threshold_power = 10
            if this_power > threshold_power:
                next_power = threshold_power + 3
                while next_power < this_power:
                    print("SETTING To...",next_power)
                    b.set_power(next_power)
                    time.sleep(3.0)
                    next_power += 3
            b.set_power(this_power)
        else:
            b.set_power(this_power)
        time.sleep(15)
        with prologix_connection() as p:
            with gigatronics(prologix_instance=p, address=7) as g:
                meter_powers[j] = g.read_power()
                print("POWER READING",meter_powers[j])
        run_cpmg(
                nScans = values['nScans'],
                indirect_idx = j+1,
                indirect_len = len(powers) +1,
                ph1_cyc = ph1_cyc,
                adcOffset = values['adc_offset'],
                carrierFreq_MHz = values['carrierFreq_MHz'],
                nPoints = nPoints,
                nEchoes = values['nEchoes'],
                p90_us = values['p90_us'],
                repetition_us = values['repetition_us'],
                pad_start_us = pad_start,
                pad_end_us = pad_end,
                tau_us = tau_us,
                SW_kHz = values['SW_kHz'],
                output_name = filename,
                ret_data = cpmg_data)
        last_power = this_power
SpinCore_pp.stopBoard();
#}}}
#{{{save and show data
DNP_data.set_prop('acq_params',values)
DNP_data.name(values['type'])
DNP_data.chunk('t',['ph1','t2'],[len(ph1_cyc),-1])
DNP_data.setaxis('ph1',len(ph1_cyc)/4)
DNP_data.hdf5_write(myfilename,
        directory=getDATADIR(exp_type='ODNP_NMR_comp/DNP'))
fl.next('raw data')
fl.image(DNP_data)
fl.next('abs raw data')
fl.image(abs(DNP_data))
data.ft('t',shift=True)
fl.next('raw data - ft')
fl.image(DNP_data)
fl.next('abs raw data - ft')
fl.image(abs(DNP_data))
fl.show()
#}}}
