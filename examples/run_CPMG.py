from pylab import *
from pyspecdata import *
from numpy import *
import SpinCore_pp 
from datetime import datetime
fl = figlist_var()

date = datetime.now().strftime('%y%m%d')
output_name = 'TEMPOL_capProbe'
node_name = 'CPMG_4step_6'
adcOffset = 25
carrierFreq_MHz = 14.895548
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
p90_us = 4.477
deadtime_us = 10.0
repetition_us = 12e6
deblank_us = 1.0
marker = 1.0

SW_kHz = 2.0
nPoints = 64
acq_time_ms = nPoints/SW_kHz # ms

tau_extra = 1000.0 # us, must be more than deadtime and more than deblank
pad_start = tau_extra - deadtime_us
pad_end = tau_extra - deblank_us*2 # marker + deblank
twice_tau = deblank_us + 2*p90_us + deadtime_us + pad_start + acq_time_ms*1e3 + pad_end + marker
tau_us = twice_tau/2.0

nScans = 16
nEchoes = 64
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 4
    ph1_cyc = r_[0, 1, 2, 3]
if not phase_cycling:
    nPhaseSteps = 1 
data_length = 2*nPoints*nEchoes*nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
data = run_cpmg(
        nScans=nScans,
        indirect_idx = 0,
        ph1_cyc = ph1_cyc,
        adcOffset = adcOffset,
        carrierFreq_MHz = carrierFreq_MHz,
        nPoints = nPoints,
        nEchoes = nEchoes,
        p90_us = p90_us,
        repetition = repetition_us,
        tau_us = tau_us,
        SW_kHz = SW_kHz,
        pad_start_us = pad_start,
        pad_end_us = pad_end,
        output_name = output_name,
        ret_data = None)
acq_params = {j: eval(j) for j in dir() if j in [
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
        "nPhaseSteps",
        ]
        }
data.set_prop("acq_params",acq_params)
data.name(node_name)
data.hdf5_write(date + '_'+output_name+'.h5',
        directory=getDATADIR(exp_type = 'ODNP_NMR_comp/CPMG'))
SpinCore_pp.stopBoard();
print(ndshape(data))
s = data.C
s.set_units('t','s')
orig_t = s.getaxis('t')
acq_time_s = orig_t[nPoints]
fl.next('time')
fl.plot(abs(s))
fl.plot(s.real,alpha=0.4)
fl.plot(s.imag,alpha=0.4)
s.ft('t',shift=True)
fl.next('freq')
fl.plot(abs(s))
fl.plot(s.real,alpha=0.4)
fl.plot(s.imag,alpha=0.4)
fl.show();quit()

