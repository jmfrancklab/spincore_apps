# Just capturing FID, not echo detection
# 4-step phase cycle
from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
from datetime import datetime
import numpy as np
import h5py
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
from ppg import generic

target_directory = getDATADIR(exp_type="ODNP_NMR_comp/Echoes")
fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "FID"
config_dict["date"] = date
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{ phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0,1,2,3]
    nPhaseSteps = 4
if not phase_cycling:
    ph1_cyc = 0.0
    nPhaseSteps = 1
# }}}
# {{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
# }}}
# {{{ppg
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
data = generic(
        ppg_list = [
            ("marker", "start", 1),
            ("phase_reset", 1),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", config_dict["p90_us"], "ph1", ph1_cyc),
            ("delay", config_dict["deadtime_us"]),
            ("acquire", config_dict["acq_time_ms"]),
            ("delay", config_dict["repetition_us"]),
            ("jumpto", "start")],
        nScans = config_dict['nScans'],
        indirect_len = 1,
        indirect_idx = 0,
        adcOffset = config_dict['adc_offset'],
        carrierFreq_MHz = config_dict['carrierFreq_MHz'],
        nPoints = nPoints,
        SW_kHz - config_dict['SW_kHz'],
        ret_data = None
        )
# }}}
# {{{ saving data
if phase_cycling:
    data.chunk("t", ["ph1", "t2"], [len(ph1_cyc), -1])
    data.setaxis("ph1", ph1_cyc / 4)
    if config_dict["nScans"] > 1:
        data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    data.reorder(["ph1", "nScans", "t2"])
    data.squeeze()
    data.set_units("t2", "s")
    fl.next("Raw - time")
    fl.image(data.C.mean("nScans"))
    data.reorder("t2", first=False)
    for_plot = data.C
    for_plot.ft("t2", shift=True)
    for_plot.ft(["ph1"], unitary=True)
    fl.next("FTed data")
    fl.image(for_plot.C.mean("nScans"))
else:
    if config_dict["nScans"] > 1:
        data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    data.rename("t", "t2")
    fl.next("Raw - time")
    fl.image(data.C.mean("nScans"))
    data.reorder("t2", first=False)
    for_plot = data.C
    for_plot.ft("t2", shift=True)
    fl.next("FTed data")
    fl.image(for_plot)
data.name(config_dict["type"] + "_" + str(config_dict["echo_counter"]))
data.set_prop("acq_params", config_dict.asdict())
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/Echoes")
filename_out = filename + ".h5"
nodename = data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_FID")
            data.name("temp_FID")
            nodename = "temp_FID"
    data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_FID.h5 in the current directory"
        )
        if os.path.exists("temp_FID.h5"):
            print("there is a temp_FID.h5 already! -- I'm removing it")
            os.remove("temp_FID.h5")
            data.hdf5_write("temp_FID.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_FID.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", data.name()))
config_dict.write()
fl.show()
