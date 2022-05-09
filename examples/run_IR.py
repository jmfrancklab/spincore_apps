'''Run Inversion Recovery at set power
======================================
You will need to manually set the power manually with Spyder and the B12. Once the power is set and the parameters are adjusted, you can run this program to collect the inversion recovery dataset at the set power.
'''
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp import run_IR
import socket
import sys
import time
from datetime import datetime
#init_logging(level='debug')
fl = figlist_var()
date = datetime.now().strftime('%y%m%d')
output_name = 'TEMPOL_289uM_heat_exch_0C'
node_name = 'FIR'
adcOffset = 28
carrierFreq_MHz = 14.549013
nScans = 1
nEchoes = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
p90_us = 1.781
repetition_us = 4e6
SW_kHz = 3.9
acq_ms = 1024.
nPoints = int(acq_ms*SW_kHz+0.5)
tau_us = 3500
total_pts = nPoints*nPhaseSteps
assert total_pts < 2**14, "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
print("ACQUISITION TIME:",acq_time,"ms")
print("TAU DELAY:",tau,"us")
phase_cycling = True
if phase_cycling:
    ph1 = r_[0,2]
    ph2 = r_[0,2]
    nPhaseSteps = 4
if not phase_cycling:
    ph1 = r_[0]
    ph2 = r_[0]
    nPhaseSteps = 1 
data_length = 2*nPoints*nEchoes*nPhaseSteps
vd_list_us = np.linspace(5e1,6e6,8)
# {{{ check for file
myfilename = date + "_" + output_name + ".h5"
if os.path.exists(myfilename):
    raise ValueError(
        "the file %s already exists, so I'm not going to let you proceed!" % myfilename
    )
# }}}

vd_data = run_IR(
        nPoints = nPoints,
        nEchoes=nEchoes,
        vd_list_us = vd_list_us,
        nScans=nScans,
        adcOffset = adcOffset,
        carrierFreq_MHz=carrierFreq_MHz,
        p90_us=p90_us,
        tau_us = tau_us,
        repetition=repetition_us,
        ph1_cyc = ph1,
        ph2_cyc = ph2,
        output_name=output_name,
        SW_kHz=SW_kHz,
        ret_data = None)
acq_params = {j:eval(j) for j in dir() if j in [
    "adcOffset",
    "carrierFreq_MHz",
    "amplitude",
    "nScans",
    "nEchoes",
    "p90_us",
    "deadtime_us",
    "repetition_us",
    "SW_kHz",
    "nPoints",
    "deblank_us",
    "tau_us",
    "acq_time_ms",
    "meter_power"]}
vd_data.set_prop('acq_params',acq_params)
vd_data.set_prop("postproc", "spincore_IR_v1")
vd_data.name(nodename)
if phase_cycling:
    vd_data.chunk("t",['ph1','ph2','t2'],[len(ph1),len(ph2),-1])
    vd_data.setaxis("ph1", IR_ph1_cyc / 4)
    vd_data.setaxis("ph2", IR_ph2_cyc / 4)
else:
    vd_data.rename('t','t2')
vd_data.hdf5_write(myfilename,
        directory=getDATADIR(exp_type='ODNP_NMR_comp/IR'))
SpinCore_pp.stopBoard();
vd_data.reorder(['ph1','ph2','vd','t2'])
fl.next('raw data')
fl.image(vd_data.setaxis('vd','#'))
fl.next('abs raw data')
fl.image(abs(vd_data).setaxis('vd','#'))
vd_data.ft(['ph1','ph2'])
vd_data.ft('t2',shift=True)
fl.next('FT raw data')
fl.image(vd_data.setaxis('vd','#'))
fl.next('FT abs raw data')
fl.image(abs(vd_data).setaxis('vd','#')['t2':(-1e3,1e3)])
fl.show();quit()
