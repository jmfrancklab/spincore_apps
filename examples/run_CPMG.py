"""
CPMG
====

This script will perform a standard CPMG experiment. 
In order to form a symmetric echo, a padding time is added before 
and after your tau through a series of delays. 
"""
from pylab import *
from pyspecdata import *
from numpy import *
import SpinCore_pp
from SpinCore_pp.ppg import run_cpmg
import os
from datetime import datetime
import h5py
raise RuntimeError("This pulse proram has not been updated.  Before running again, it should be possible to replace a lot of the code below with a call to the function provided by the 'generic' pulse program inside the ppg directory!")

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "CPMG"
config_dict["date"] = date
config_dict["cpmg_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{set phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0, 1, 2, 3]
    nPhaseSteps = 4
if not phase_cycling:
    ph1_cyc = 0.0
    nPhaseSteps = 1
# }}}
# {{{better tau for a perfectly symmetric echo
marker = 1.0  # 10/10/22 → what is this? → pretty sure the time needed to execute the marker command
pad_start = config_dict["tau_extra_us"] - config_dict["deadtime_us"]
pad_end = (
    config_dict["tau_extra_us"] - config_dict["deblank_us"] - marker
)  # marker + deblank
assert(pad_start > 0), "tau_extra_us must be set to more than deadtime and more than deblank!"
assert (pad_end > 0), "tau_extra_us must be set to more than deadtime and more than deblank!"
twice_tau_echo_us = (  # the period between 180 pulses
    config_dict["tau_extra_us"] * 2 + config_dict["acq_time_ms"] * 1e3
)
# now twice_tau_echo_us/2.0 is τ_echo, so I need to subtract the extra delays
# imposed by the ppg to determine the remaining τ that I need
config_dict["tau_us"] = twice_tau_echo_us / 2.0 - (
    2
    * config_dict["p90_us"]
    / pi  # evolution during pulse -- see eq 6 of coherence paper
    + config_dict["deadtime_us"]  # following 90
    + config_dict["deblank_us"]  # before 180
)
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2 ** 14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
# {{{run cpmg
# NOTE: Number of segments is nEchoes * nPhaseSteps
data = run_cpmg(
    nScans = config_dict["nScans"],
    indirect_idx = 0,
    indirect_len = 1,
    ph1_cyc = ph1_cyc,
    adcOffset = config_dict["adc_offset"],
    carrierFreq_MHz = config_dict["carrierFreq_MHz"],
    nPoints = nPoints,
    nEchoes = config_dict["nEchoes"],
    p90_us = config_dict["p90_us"],
    repetition_us = config_dict["repetition_us"],
    tau_us = config_dict["tau_us"],
    SW_kHz = config_dict["SW_kHz"],
    pad_start_us = pad_start,
    pad_end_us = pad_end,
    ret_data = None,
)
# }}}
# {{{ chunk and save data
if phase_cycling:
    data.chunk("t", ["ph1", "echo", "t2"], [len(ph1_cyc), config_dict["nEchoes"], -1])
    data.setaxis("ph1", ph1_cyc / 4)
    data.setaxis("echo", r_[0 : config_dict["nEchoes"]])
    if config_dict["nScans"] > 1:
        data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    data.squeeze()
    data.set_units("t2", "s")
    fl.next("Raw - time")
    fl.image(
        data.C.mean("nScans"))
    data.reorder("t2", first=False)
    for_plot = data.C
    for_plot.ft('t2',shift=True)
    for_plot.ft(['ph1'], unitary = True)
    fl.next('FTed data')
    fl.image(for_plot.C.mean("nScans")
    )
else:
    if config_dict["nScans"] > 1:
        data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    data.rename("t","t2")
    fl.next("Raw - time")
    fl.image(
        data.C.mean("nScans"))
    data.reorder("t2", first=False)
    for_plot = echo_data.C
    for_plot.ft('t2',shift=True)
    fl.next('FTed data')
    fl.image(for_plot)
data.name(config_dict["type"] + "_" + config_dict["cpmg_counter"])
data.set_prop("postproc_type", "spincore_CPMGv2")
data.set_prop("acq_params", config_dict.asdict())
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/CPMG")
filename_out = filename + ".h5"
nodename = data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_cpmg")
            data.name("temp_cpmg")
            nodename = "temp_cpmg"
    data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_cpmg.h5 in the current h5 file"
        )
        if os.path.exists("temp_cpmg.h5"):
            print("there is a temp_cpmg.h5 already! -- I'm removing it")
            os.remove("temp_cpmg.h5")
            data.hdf5_write("temp_cpmg.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_cpmg.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", data.name()))
config_dict.write()
fl.show()
