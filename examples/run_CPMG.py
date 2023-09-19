"""
CPMG
====

This script will perform a standard CPMG experiment. 
In order to form a symmetric echo, a padding time is added before 
and after your tau. 
"""
from pylab import *
from pyspecdata import *
from numpy import *
import SpinCore_pp
from SpinCore_pp.ppg import run_cpmg
import os
from datetime import datetime
import h5py

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
    ph1_cyc = r_[0, 2, 1, 3, 2, 4, 3, 5]
    ph2_cyc = [0, 0, 1, 1, 2, 2, 3, 3]
    nPhaseSteps = 8

if not phase_cycling:
    ph1_cyc = 0.0
    nPhaseSteps = 1
# }}}
# {{{symmetric tau
marker = 1.0
jumpto = 1.0
x_us = 2500.0 #must be more than deadtime and more than deblanking time
pad_start = x_us - config_dict['deadtime_us']
pad_end = x_us - config_dict['deblank_us'] - marker - jumpto
twice_tau_echo_us = (  # the period between end of first 180 pulse and start of next
    config_dict['deadtime_us'] + pad_start + config_dict["acq_time_ms"] * 1e3 + pad_end + marker + config_dict['deblank_us']
)
config_dict["tau_us"] = twice_tau_echo_us / 2.0 + (
    2
    * config_dict["p90_us"]
    / pi  # evolution during pulse -- see eq 6 of coherence paper
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
data = generic(
        ppg_list = [
                ("phase_reset", 1),
                ("delay_TTL", config_dict['deblank_us']),
                ("pulse_TTL", config_dict['p90_us'], "ph1", ph1_cyc),
                ("delay", tau_us),
                ("delay_TTL", config_dict['deblank_us']),
                ("pulse_TTL", 2.0 * config_dict['p90_us'], "ph2", ph2_cyc),
                ("delay", config_dict['deadtime_us']),
                ("delay", pad_start),
                ("acquire", config_dict['acq_time_ms']),
                ("delay", pad_end),
                ("delay",1.0), #matching the jumpto delay
                ("marker", "echo_label", (config_dict['nEchoes'] - 1)), 
                ("delay_TTL", config_dict['deblank_us']),
                ("pulse_TTL", 2.0 * config_dict['p90_us'], 0.0),
                ("delay", config_dict['deadtime_us']),
                ("delay", pad_start_us),
                ("acquire", config_dict['acq_time_ms']),
                ("delay", pad_end),
                ("jumpto", "echo_label"), 
                ("delay", config_dict['repetition_us']),
                ("jumpto","start")
            ],
        nScans = config_dict["nScans"],
        indirect_idx = 0,
        indirect_len = len(config_dict['nEchoes']),
        adcOffset = config_dict["adc_offset"],
        carrierFreq_MHz = config_dict["carrierFreq_MHz"],
        nPoints = nPoints,
        SW_kHz = config_dict["SW_kHz"],
        ret_data = None,
    )
# }}}
# {{{ chunk and save data
data.chunk("t", ["ph1", "ph2", "tE", "t2"], [len(ph1_cyc), len(ph2_cyc), config_dict["nEchoes"], -1])
data.setaxis("ph1", ph1_cyc / len(ph1_cyc)
data.setaxis("ph2", ph2_cyc / len(ph2_cyc)
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
