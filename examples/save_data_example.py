"""
test of logging
===============

This test of the logging mimics an ODNP field sweep experiment.
"""
from numpy import *
from numpy.random import rand
from pyspecdata import *
from Instruments import *
import os
import sys
import time
import random
long_delay = 1e-3
short_delay = 1e-4
def gen_powerlist(max_power, steps, min_dBm_step=0.5):
    "generate a list of (roughly) evenly spaced powers up to max_power"
    lin_steps = steps
    def det_allowed(lin_steps):
        powers = r_[0:max_power:1j*lin_steps][1:]
        vectorize(powers)
        rdB_settings = ones_like(powers)
        for x in range(len(powers)):
            rdB_settings[x] = round(10*(log10(powers[x])+3.0)/min_dBm_step)*min_dBm_step # round to nearest min_dBm_step
        return unique(rdB_settings)
    dB_settings = det_allowed(lin_steps)
    while len(dB_settings) < steps-1:
        lin_steps += 1
        dB_settings = det_allowed(lin_steps)
        if lin_steps >= 200:
            raise ValueError("I think I'm in an infinite loop -- maybe you"
                    "can't request %d steps between 0 and %f W without going"
                    "below %f a step?")%(steps,max_power,min_dBm_step)
    return dB_settings
#{{{ params for Bridge 12/power
dB_settings = gen_powerlist(4,25.0)
powers =1e-3*10**(dB_settings/10.)
#}}}
#{{{ time of pulse prog
DNP_data = None
#{{{ pulse prog
def run_scans(nScans, power_idx, field_idx, DNP_data=None):
    ph1_cyc = r_[0,1,2,3]
    ph2_cyc = r_[0]
    nPhaseSteps = len(ph1_cyc)*len(ph2_cyc)
    data_length = 2*2048*1*nPhaseSteps
    for x in range(nScans):
        raw_data = np.random.random(2048) + np.random.random(2048) * 1j#SpinCore_pp.getData(data_length, nPoints, nEchoes, nPhaseSteps, output_name)
        data_array = complex128(raw_data[0::2]+1j*raw_data[1::2])
        dataPoints = int(shape(data_array)[0])
        if DNP_data is None and power_idx ==0 and field_idx == 0:
            time_axis = linspace(0.0,1*nPhaseSteps*85.3*1e-3,dataPoints)
            DNP_data = ndshape([len(powers),len(r_[3501:3530:0.001]),1,dataPoints],['power','field','nScans','t']).alloc(dtype=complex128)
            DNP_data.setaxis('power',r_[powers]).set_units('W')
            DNP_data.setaxis('field',r_[3501:3530:0.001]).set_units('G')
            DNP_data.setaxis('t',time_axis).set_units('t','s')
            DNP_data.setaxis('nScans',r_[0:1])
            DNP_data.name("node_name")
        DNP_data['power',power_idx]['field',field_idx]['nScans',x] = data_array
        if nScans > 1:
            DNP_data.setaxis('nScans',r_[0:1])
        return DNP_data
#}}}

#}}}
#{{{where error occurs
meter_powers = zeros_like(dB_settings)
carrierFreqs_MHz = zeros_like(r_[3501:3530:0.001], dtype=float)
fields_Set = zeros_like(r_[3501:3530:0.001],dtype=float)

with power_control() as p:
    for j,this_dB in enumerate(dB_settings):
        print("I'm going to pretend to run",this_dB,"dBm")
        if j == 0:
            time.sleep(short_delay)
            p.start_log()
        p.set_power(this_dB)
        for k in range(10):
            time.sleep(short_delay)
            if p.get_power_setting() >= this_dB: break
        time.sleep(long_delay)
        meter_powers[j] = p.get_power_setting()
        if True:
            # the following seems unrealistic for a field sweep -- what's
            # up with that?
            for B0_index,desired_B0 in enumerate(r_[3501:3530:0.001]):
                #carrierFreq_MHz = rand()
                carrierFreqs_MHz[B0_index] = rand()
                fields_Set[B0_index] = rand()
                time.sleep(short_delay)
                if True:
                    DNP_data = run_scans(1,j,B0_index,DNP_data)
                    time.sleep(long_delay)
    log_array, log_dict = p.stop_log()# where error occurred originally!
print("EXITING...")    
#}}}

