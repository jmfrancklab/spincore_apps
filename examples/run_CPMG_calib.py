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
from pyspecdata import *
from numpy import *
from . import SpinCore_pp 
fl = figlist_var()

date = '200115'
output_name = 'CPMG_calib_3'
adcOffset = 45
carrierFreq_MHz = 14.898122
tx_phases = r_[0.0,90.0,180.0,270.0]
amplitude = 1.0
deadtime_us = 100.0
repetition_us = 15e6
deblank_us = 1.0
marker = 1.0

SW_kHz = 4.0
nPoints = 128
acq_time_ms = nPoints/SW_kHz # ms

tau_extra = 200.0 # us, must be more than deadtime and more than deblank
pad_start = tau_extra - deadtime_us
pad_end = tau_extra - deblank_us*2 # marker + deblank

nScans = 4
nEchoes = 64

nPhaseSteps = 2
ph1_cyc = r_[0,2]
data_length = 2*nPoints*nEchoes*nPhaseSteps
p90_range = linspace(3.0,4.0,5)#,endpoint=False)
# NOTE: Number of segments is nEchoes * nPhaseSteps
for index,val in enumerate(p90_range):
    p90 = val # us
    twice_tau = deblank_us + 2*p90_us + deadtime_us + pad_start + acq_time_ms*1e3 + pad_end + marker
    tau_us = twice_tau/2.0
    print("***")
    print("INDEX %d - 90 TIME %f"%(index,val))
    print("***")
    if index == 0:
        nutation_data = run_cpmg(
                nScans=nScans,
                indirect_idx = 0,
                indirect_len = len(p90_range)+1,
                adcOffset = adcOffset,
                carrierFreq_MHz=carrierFreq_MHz,
                nPoints=nPoints,
                nEchoes = nEchoes,
                p90_us = p90,
                repetition_us = repetition_us,
                pad_start_us = pad_start,
                pad_end_us = pad_end,
                tau_us = tau_us,
                SW_kHz=SW_kHz,
                output_name=output_name,
                ph1_cyc = ph1_cyc,
                ret_data = None)
    else:
         run_cpmg(
                nScans=nScans,
                indirect_idx = index+1,
                indirect_len = len(p90_range+1),
                adcOffset = adcOffset,
                carrierFreq_MHz=carrierFreq_MHz,
                nPoints=nPoints,
                nEchoes = nEchoes,
                p90_us = p90,
                repetition_us = repetition_us,
                pad_start_us = pad_start,
                pad_end_us = pad_end,
                tau_us = tau_us,
                SW_kHz=SW_kHz,
                output_name=output_name,
                ph1_cyc = ph1_cyc,
                ret_data = nutation_data)
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
nutation_data.set_prop("acq_params",acq_params)
nutation_data.name('nutation')
nutation_data.chunk('t',['ph1','t2'],[len(ph1_cyc),-1])
nutation_data.setaxis('ph1',ph1_cyc/4)
nutation_data.hdf5_write(date+'_'+output_name+'.h5')
SpinCore_pp.stopBoard();
fl.next('raw data')
fl.image(nutation_data)
nutation_data.ft('t',shift=True)
fl.next('FT raw data')
fl.image(nutation_data)
fl.show()
