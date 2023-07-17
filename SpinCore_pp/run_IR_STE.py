"""Inversion recovery with a stimulated echo
============================================
Inversion recovery followed by stimulated echo with a linearly spaced vd list made based off of parameters in the configuration file
"""
from pylab import *
from pyspecdata import *
import os, sys
import SpinCore_pp
from datetime import datetime
import numpy as np
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
from Instruments.XEPR_eth import xepr
import h5py

fl = figlist_var()
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/inv_rec")
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "IR_STE"
config_dict["date"] = date
config_dict["IR_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{let computer set field
print(
    "I'm assuming that you've tuned your probe to",
    config_dict["carrierFreq_MHz"],
    "since that's what's in your .ini file",
)
Field = config_dict["carrierFreq_MHz"] / config_dict["gamma_eff_MHz_G"]
print(
    "Based on that, and the gamma_eff_MHz_G you have in your .ini file, I'm setting the field to %f"
    % Field
)
with xepr() as x:
    assert Field < 3700, "are you crazy??? field is too high!"
    assert Field > 3300, "are you crazy?? field is too low!"
    Field = x.set_field(Field)
    print("field set to ", Field)
# }}}
# {{{phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0, 2]
    ph2_cyc = r_[0, 2]
    ph3_cyc = r_[0, 2]
    nPhaseSteps = 8
else:
    ph1_cyc = 0.0
    ph2_cyc = 0.0
    ph3_cyc = 0.0
    nPhaseSteps = 1
# }}}
# {{{ note on timing
# putting all times in mic
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
# }}}
# {{{tau and vd list
tau1 = 2
tau2 = 80000
# {{{make vd list
vd_kwargs = {
    j: config_dict[j]
    for j in ["krho_cold", "krho_hot", "T1water_cold", "T1water_hot"]
    if j in config_dict.keys()
}
vd_list_us = (
    SpinCore_pp.vdlist_from_relaxivities(config_dict["concentration"], **vd_kwargs)
    * 1e6
)  # put vd list into microseconds
# }}}
# }}}
# {{{ run ppg
print(("TAU 1 DELAY:", tau1, "us"))
print(("TAU 2 DELAY:", tau2, "us"))
data_length = 2 * nPoints * nEchoes * nPhaseSteps
vd_data = None
for vd_index, vd_val in enumerate(vd_list):
    vd_data = generic(
        ppg_list=[
            ("marker", "start", 1),
            ("phase_reset", 1),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", 2.0 * config_dict["p90_us"], 0),
            ("delay", vd),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", config_dict["p90_us"], "ph1", phy_cyc),
            ("delay", tau1),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", config_dict["p90_us"], "ph2", ph2_cyc),
            ("delay", tau2),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", config_dict["p90_us"], "ph3", ph3_cyc),
            ("delay", config_dict["deadtime_us"]),
            ("acquire", config_dict["acq_time_ms"]),
            ("delay", config_dict["repetition_us"]),
            ("jumpto", "start"),
        ],
        nScans=config_dict["nScans"],
        indirect_idx=0,
        indirect_len=1,
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        SW_kHz=config_dict["SW_kHz"],
        ret_data=vd_data,
    )
    vd_data.set_prop("acq_params", config_dict.asdict())
    vd_data.rename("indirect", "vd")
    vd_data.setaxis("vd", vd_list_us * 1e-6).set_units("vd", "s")
    if phase_cycling:
        vd_data.chunk(
            "t",
            ["ph1", "ph2", "ph3", "t2"],
            [len(ph1_cyc), len(ph2_cyc), len(ph3_cyc), -1],
        )
        vd_data.setaxis("ph1", ph1_cyc / 4)
        vd_data.setaxis("ph2", ph2_cyc / 4)
        vd_data.setaxis("ph3", ph3_cyc / 4)
    else:
        vd_data.rename("t", "t2")
    if configdict["nScans"] > 1:
        vd_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    vd_data.reorder(["ph1", "ph2", "ph3", "nScans", "vd", "t2"])
    vd_data.squeeze()
    vd_datan.set_units("t2", "s")
    fl.next("Raw data - time domain")
    fl.image(vd_data)
    for_plot = vd_data.C
    for_plot.ft("t2", shift=True)
    for_plot.ft(["ph1", "ph2", "ph3"], unitary=True)
    fl.next("Raw data - frequency domain")
    fl.image(for_plot)
# }}}
# {{{ save data
vd_data.name(config_dict["type"])
nodename = data.name()
filename_out = filename + ".h5"
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_IR_STE")
            vd_data.name("temp_IR_STE")
            nodename = "temp_IR_STE"
    vd_data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        vd_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_IR_STE.h5 in the current directory"
        )
        if os.path.exists("temp_IR_STE.h5"):
            print("there is a temp_IR_STE.h5 already! -- I'm removing it")
            os.remove("temp_IR_STE.h5")
            echo_data.hdf5_write("temp_IR_STE.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_IR_STE.h5 to the correct name!!"
            )
        if os.path.exists("temp_IR_STE.h5"):
            print("there is a temp_IR_STE.h5 -- I'm removing it")
            os.remove("temp_IR_STE.h5")
        vd_data.hdf5_write("temp_IR_STE.h5")
        print(
            "if I got this far, that probably worked -- be sure to move/rename temp_IR_STE.h5 to the correct name!!"
        )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", vd_data.name()))
config_dict.write()
# }}}
# {{{ image data
data.set_units("t", "data")
data.chunk("t", ["ph3", "ph2", "ph1", "t2"], [2, 2, 2, -1])
data.setaxis("ph3", r_[0.0, 2.0] / 4)
data.setaxis("ph2", r_[0.0, 2.0] / 4)
data.setaxis("ph1", r_[0.0, 2.0] / 4)
if nScans > 1:
    data.setaxis("nScans", r_[0 : config_dict["nScans"]])
fl.next("image")
data.mean("nScans")
fl.image(data)
data.ft("t2", shift=True)
fl.next("image - ft")
fl.image(data)
fl.next("image - ft, coherence")
data.ft(["ph1", "ph2", "ph3"])
fl.image(data)
fl.next("image - ft, coherence, exclude FID")
fl.image(data["ph1", 1]["ph3", -1])
fl.show()
# }}}
