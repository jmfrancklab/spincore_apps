"""
CPMG_calibration
================
Here we can calibrate our 90 time and tau by cycling through 90 times (which are defined as a list in this script) and thus tau is fixed accordingly to maintain symmetric echoes.

"""
from pyspecdata import *
from numpy import *
from datetime import datetime
import SpinCore_pp
from SpinCore_pp.ppg import generic
import h5py

fl = figlist_var()
p90_range = linspace(3.0, 4.0, 5)
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "CPMG_calib"
config_dict["date"] = date
config_dict["cpmg_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{set phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0, 2]
    nPhaseSteps = 2
if not phase_cycling:
    ph1_cyc = 0.0
    nPhaseSteps = 1
# }}}
# {{{making tau for a symmetric echo given delays
marker = 1.0
pad_start = config_dict["tau_extra_us"] - config_dict["deadtime_us"]
pad_end = config_dict["tau_extra_us"] - config_dict["deblank_us"] - marker
assert (
    pad_start > 0
), "tau_extra_us must be set to more than deadtime and more than deblank!"
assert (
    pad_end > 0
), "tau_extra_us must be set to more than deadtime and more than deblank!"
twice_tau_echo_us = (  # the period between 180 pulses
    config_dict["tau_extra_us"] * 2 + config_dict["acq_time_ms"] * 1e3
)
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2**14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
# {{{run ppg
for index, val in enumerate(p90_range):
    p90_us = val  # us
    this_tau = twice_tau_echo_us / 2.0 - (
        2 * p90 / pi  # evolution during pulse -- see eq 6 of coherence paper
        + config_dict["deadtime_us"]  # following 90
        + config_dict["deblank_us"]  # before 180
    )

    print("***")
    print("INDEX %d - 90 TIME %f" % (index, val))
    print("***")
    if index == 0:
        data = generic(
            ppg_list=[
                ("phase_reset", 1),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", config_dict["p90_us"], "ph1", ph1_cyc),
                ("delay", this_tau),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
                ("delay", config_dict["deadtime_us"]),
                ("delay", pad_start_us),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", pad_end_us),
                ("marker", "echo_label", (config_dict["nEchoes"] - 1)),  # 1 us delay
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
                ("delay", config_dict["deadtime_us"]),
                ("delay", pad_start_us),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", pad_end_us),
                ("jumpto", "echo_label"),  # 1 us delay
                ("delay", config_dict["repetition_us"]),
            ],
            nScans=config_dict["nScans"],
            indirect_idx=0,
            indirect_len=len(p90_range) + 1,
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            SW_kHz=config_dict["SW_kHz"],
            indirect_fields=("tau", "p90_us"),
            ret_data=None,
        )
        p90_axis = data.getaxis("indirect")
        p90_axis[0]["tau"] = this_tau
        p90_axis[0]["p90_us"] = p90
    else:
        generic(
            ppg_list=[
                ("phase_reset", 1),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", config_dict["p90_us"], "ph1", ph1_cyc),
                ("delay", this_tau),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
                ("delay", config_dict["deadtime_us"]),
                ("delay", pad_start_us),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", pad_end_us),
                ("marker", "echo_label", (config_dict["nEchoes"] - 1)),  # 1 us delay
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
                ("delay", config_dict["deadtime_us"]),
                ("delay", pad_start_us),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", pad_end_us),
                ("jumpto", "echo_label"),  # 1 us delay
                ("delay", config_dict["repetition_us"]),
            ],
            nScans=config_dict["nScans"],
            indirect_idx=index + 1,
            indirect_len=len(p90_range + 1),
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            SW_kHz=config_dict["SW_kHz"],
            indirect_fileds=("tau", "p90_us"),
            ret_data=data,
        )
        p90_axis[index + 1]["p90_us"] = p90
        p90_axis[index + 1]["tau"] = this_tau
# }}}
# {{{Save data
data.name(config_dict["type"] + "_" + config_dict["cpmg_counter"])
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
            print("this nodename already exists, so I will call it temp_cpmg_calib")
            data.name("temp_cpmg_calib")
            nodename = "temp_cpmg_calib"
    data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_cpmg_calib.h5 in the current directory"
        )
        if os.path.exists("temp_cpmg_echo.h5"):
            print("there is a temp_cpmg_calib.h5 already! -- I'm removing it")
            os.remove("temp.h5")
            data.hdf5_write("temp.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", data.name()))
config_dict.write()
