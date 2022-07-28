# {{{ note on phase cycling
"""
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
"""
# }}}
from pyspecdata import *
from numpy import *
from datetime import datetime
from . import SpinCore_pp

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "CPMG_calib"
config_dict["date"] = date
config_dict["echo_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
marker = 1.0
tau_extra = 200.0  # us, must be more than deadtime and more than deblank
pad_start = tau_extra - config_dict["deadtime_us"]
pad_end = tau_extra - config_dict["deblank_us"] * 2
nPhaseSteps = 2
ph1_cyc = r_[0, 2]
p90_range = linspace(3.0, 4.0, 5)  # ,endpoint=False)
# NOTE: Number of segments is nEchoes * nPhaseSteps
for index, val in enumerate(p90_range):
    p90 = val  # us
    twice_tau = (
        config_dict["deblank_us"]
        + 2 * p90
        + config_dict["deadtime_us"]
        + pad_start
        + config_dict["acq_time_ms"] * 1e3
        + pad_end
        + marker
    )
    tau_us = twice_tau / 2.0
    print("***")
    print("INDEX %d - 90 TIME %f" % (index, val))
    print("***")
    if index == 0:
        nutation_data = run_cpmg(
            nScans=config_dict["nScans"],
            indirect_idx=0,
            indirect_len=len(p90_range) + 1,
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            p90_us=p90_us,
            repetition_us=config_dict["repetition_us"],
            pad_start_us=pad_start,
            pad_end_us=pad_end,
            tau_us=tau_us,
            SW_kHz=config_dict["SW_kHz"],
            output_name=filename,
            ph1_cyc=ph1_cyc,
            ret_data=None,
        )
    else:
        run_cpmg(
            nScans=config_dict["nScans"],
            indirect_idx=index + 1,
            indirect_len=len(p90_range + 1),
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            p90_us=p90,
            repetition_us=config_dict["repetition_us"],
            pad_start_us=pad_start,
            pad_end_us=pad_end,
            tau_us=tau_us,
            SW_kHz=config_dict["SW_kHz"],
            output_name=filename,
            ph1_cyc=ph1_cyc,
            ret_data=nutation_data,
        )
SpinCore_pp.stopBoard()
nutation_data.set_prop("acq_params", config_dict.asdict())
nutation_data.name(config_dict["type"] + "_" + config_dict["cpmg_counter"])
nutation_data.chunk("t", ["ph1", "t2"], [len(ph1_cyc), -1])
nutation_data.setaxis("ph1", ph1_cyc / 4)
if config_dict["nScans"] > 1:
    nutation_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/CPMG")
filename_out = filename + ".h5"
nodename = nutation_data.name()
if os.path.exists(filename + ".h5"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp")
            nutation_data.name("temp")
            nodename = "temp"
    nutation_data.hdf5_write(f"{filename_out}/{nodename}", directory=target_directory)
else:
    nutation_data.hdf5_write(filename + ".h5", directory=target_directory)
fl.next("raw data")
fl.image(nutation_data)
nutation_data.ft("t", shift=True)
fl.next("FT raw data")
fl.image(nutation_data)
fl.show()
