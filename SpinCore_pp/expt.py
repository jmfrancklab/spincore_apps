from pyspecdata import *
import numpy as np

rd = 8e6*1e-6
nScans = 1
nPhaseSteps = 8

FIR = True
#{{{
if FIR:
    vd_list = (np.linspace(5e1,12e6,12))*1e-6
    #vd_list = r_[5e1,1.8e4,3.6e4,5.5e4,7.3e4,9.1e4,1.8e5,3.44e5,5.08e5,6.72e5,8.36e5,1e6]*1e-6
    #vd_list = r_[5e1,2e5,4e5,6e5,8e5]*1e-6
    #vd_list = (np.linspace(5e1,2.5e6,12))*1e-6
    expt = rd*nScans*nPhaseSteps*len(vd_list)+sum(vd_list*nPhaseSteps*nScans)
#}}}
ODNP = False
#{{{
if ODNP:
    power_len = 20
    power_len += 3
    delay_times = 21.
    powers = power_len*delay_times
    expt = rd*nScans*nPhaseSteps*power_len+powers
#}}}
print("Estimated experiment time:",expt/60.,"min.")
