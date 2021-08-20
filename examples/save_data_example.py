from numpy import *
from pyspecdata import *
import os
import sys
import SpinCore_pp
import time
from Instruments import power_control
from Instruments import Bridge12,prologix_connection,gigatronics
from Instruments.XEPR_eth import xepr
from SpinCore_pp.power_helper import gen_powerlist
#{{{ params for Bridge 12/power
dB_settings = gen_powerlist(4,25)
#}}}
#{{{ time of pulse prog
time.sleep(15e6)
#}}}
#{{{where error occurs
meter_powers = zeros_like(dB_settings)
with power_control() as p:
    for j,this_dB in enumerate(dB_settings):
        if j == 0:
            p.start_log()
        p.set_power(this_dB)
        for k in range(10):
            time.sleep(0.5)
            if p.get_power_setting() >= this_dB: break
        if p.get_power_setting() < this_dB: raise ValueError("After 10 tries, the power has still not settled")
        time.sleep(5)
        meter_powers[j] = p.get_power_setting()
        for B0_index,desired_B0 in enumerate(r_[3503:3508:0.1]):
            time.sleep(3.0)
    log_array, log_dict = p.stop_log()# where error occurred originally!
    #}}}

