from pylab import *
from pyspecdata import *
from numpy import *
import SpinCore_pp
from datetime import datetime

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{generate filename info for config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "CPMG"
config_dict["date"] = f"{date}"
config_dict["cpmg_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{better tau
marker = 1.0  # 10/10/22 → what is this? → pretty sure the time needed to execute the marker command
pad_start = config_dict["tau_extra_us"] - config_dict["deadtime_us"]
pad_end = (
    config_dict["tau_extra_us"] - config_dict["deblank_us"] - marker
)  # marker + deblank
assert (
    pad_start > 0
), "tau_extra_us must be set to more than deadtime and more than deblank!"
assert (
    pad_end > 0
), "tau_extra_us must be set to more than deadtime and more than deblank!"
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
# {{{phase cycling
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 4
    ph1_cyc = r_[0, 1, 2, 3]
if not phase_cycling:
    nPhaseSteps = 1
# }}}
# {{{run cpmg
# NOTE: Number of segments is nEchoes * nPhaseSteps
data = run_cpmg(
    nScans=config_dict["nScans"],
    indirect_idx=0,
    ph1_cyc=ph1_cyc,
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    nEchoes=config_dict["nEchoes"],
    p90_us=config_dict["p90_us"],
    repetition=config_dict["repetition_us"],
    tau_us=config_dict["tau_us"],
    SW_kHz=config_dict["SW_kHz"],
    pad_start_us=pad_start,
    pad_end_us=pad_end,
    ret_data=None,
)
# }}}
# {{{saving with acq params
data.set_prop("acq_params", config_dict.asdict())
data.name(config_dict["type"] + "_" + config_dict["cpmg_counter"])
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/CPMG")
filename_out = filename + ".h5"
nodename = data.name()
data.set_prop("postproc_type", "spincore_CPMGv2")
if phase_cycling:
    data.chunk("t", ["ph1", "echo", "t2"], [len(ph1_cyc), config_dict["nEchoes"], -1])
    data.setaxis("echo", r_[0 : config_dict["nEchoes"]])
    data.setaxis("ph1", ph1_cyc / 4)
    if config_dict["nScans"] > 1:
        data.setaxis("nScans", r_[0 : config_dict["nScans"]])
if os.path.exists(filename + ".h5"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp")
            data.name("temp")
            nodename = "temp"
        data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp.h5 in the current directory"
        )
        if os.path.exists("temp.h5"):
            print("there is a temp.h5 already! -- I'm removing it")
            os.remove("temp.h5")
            data.hdf5_write("temp.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!"
            )
config_dict.write()
# }}}
