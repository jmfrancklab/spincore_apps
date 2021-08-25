from numpy import *
from pyspecdata import *
from Instruments import *
import os
import sys
import time
long_delay = time.sleep(5)
short_delay = time.sleep(0.1)
#from SpinCore_pp.power_helper import gen_powerlist
#{{{ params for Bridge 12/power
"Helper functions for dealing with powers"
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
dB_settings = gen_powerlist(4,25) 
#}}}
#{{{ time of pulse prog
print("sleep")
long_delay
#}}}
print("after sleep")
#{{{where error occurs
meter_powers = zeros_like(dB_settings)
with power_control() as p:
    for j,this_dB in enumerate(dB_settings):
        if j == 0:
            print("starting log")
            p.start_log()
        print("setting power")
        p.set_power(this_dB)
        for k in range(10):
            short_delay
        print("sleeping again")
        short_delay
        for B0_index,desired_B0 in enumerate(r_[3503:3508:0.1]):
            short_delay
    log_array, log_dict = p.stop_log()# where error occurred originally!
    #}}}

