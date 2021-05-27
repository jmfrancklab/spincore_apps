from pyspecdata import *
import numpy as np

rd = 10e6*1e-6
nScans = 1
nPhaseSteps = 2*2

FIR = False
#{{{
if FIR:
    vd_list = (np.linspace(5e1,10e6,12))*1e-6
    #r_[5e1,1.8e4,3.6e4,5.5e4,7.3e4,9.1e4,1.8e5,3.44e5,5.08e5,6.72e5,8.36e5,1e6]*1e-6
    expt = rd*nScans*nPhaseSteps*len(vd_list)+sum(vd_list*nPhaseSteps*nScans)
#}}}
ODNP = True
#{{{
if ODNP:
    power_len = 25
    power_len += 3
    delay_times = 19.
    powers = power_len*delay_times
    expt = rd*nScans*nPhaseSteps*power_len+powers
#}}}
print("Estimated experiment time:",expt/60.,"min.")