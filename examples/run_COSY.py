"""standard COSY experiment
===========================
parameters will be pulled from the user's configuration file. A list of t1s is made here and can easily be modified to the users needs.
"""
from pyspecdata import *
import os, time
import SpinCore_pp
from SpinCore_pp.ppg import generic
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
import h5py
from datetime import datetime

fl = figlist_var()
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/COSY")
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "COSY"
config_dict["date"] = date
config_dict["COSY_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{phase cycling and tx phases
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0, 1, 2, 3]
    ph2_cyc = r_[0, 2]
    nPhaseSteps = 8
if not phase_cycling:
    ph1_cyc = 0.0
    ph2_cyc = 0.0
    nPhaseSteps = 1
# }}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
# cannot have a delay of 0, so set to minimum SpinCore can take
# {{{making t1 list
min_t1 = 0.065  # us (lower limit of SpinCore)
max_t1 = 200 * 1e3
t1_step = 1.25 * 1e3
t1_list = r_[min_t1:max_t1:t1_step]
# }}}
# {{{ run ppg
COSY_data = generic(
    ppg_list=[
        ("marker", "start", 1),
        ("phase_reset", 1),
        ("delay_TTL", config_dict["deblank_us"]),
        ("pulse_TTL", config_dict["p90_us"], "ph1", ph1_cyc),
        ("delay", t1_list[0]),
        ("delay_TTL", config_dict["deblank_us"]),
        ("pulse_TTL", config_dict["p90_us"], "ph2", ph2_cyc),
        ("delay", config_dict["deadtime_us"]),
        ("acquire", config_dict["acq_time_ms"]),
        ("delay", config_dict["repetition_us"]),
        ("jumpto", "start"),
    ],
    nScans=config_dict["nScans"],
    indirect_idx=0,
    indirect_len=len(t1_list),
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    SW_kHz=config_dict["SW_kHz"],
    indirect_fields=("t1", "index"),
    ret_data=None,
)
myt1s = COSY_data.getaxis("indirect")
myt1s[0]["t1"] = t1_list[0]
for index, val in enumerate(t1_list[1:]):
    t1 = val
    generic(
        ppg_list=[
            ("marker", "start", 1),
            ("phase_reset", 1),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", config_dict["p90_us"], "ph1", ph1_cyc),
            ("delay", t1),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", config_dict["p90_us"], "ph2", ph2_cyc),
            ("delay", config_dict["deadtime_us"]),
            ("acquire", config_dict["acq_time_ms"]),
            ("delay", config_dict["repetition_us"]),
            ("jumpto", "start"),
        ],
        nScans=config_dict["nScans"],
        indirect_idx=index + 1,
        indirect_len=len(t1_list),
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        SW_kHz=config_dict["SW_kHz"],
        indirect_fields=("t1", "index"),
        ret_data=COSY_data,
    )
    myt1s[j + 1]["t1"] = t1
# }}}
# {{{saving data
COSY_data.set_prop("acq_params", config_dict.asdict())
COSY_data.set_prop("t1_list", t1_list)
COSY_data.name(config_dict["type"] + "_" + str(config_dict["cpmg_counter"]))
filename_out = filename + ".h5"
nodename = COSY_data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_%d" % j)
            COSY_data.name("temp_COSY_%d" % config_dict["cpmg_counter"])
            nodename = "temp_COSY_%d" % config_dict["cpmg_counter"]
            COSY_data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        COSY_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_COSY.h5 in the current directory"
        )
        if os.path.exists("temp_COSY.h5"):
            print("there is a temp_COSY.h5 already! -- I'm removing it")
            os.remove("temp_COSY.h5")
            COSY_Data.hdf5_write("temp_COSY.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_COSY.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", COSY_data.name()))
# }}}
config_dict.write()
