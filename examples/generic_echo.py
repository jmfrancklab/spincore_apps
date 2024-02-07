"""
generic echo
=============

This should generate the exact same signal as run_hahn_echo.py, but is based on the generic ppg, rather than the custom ppg.
"""
from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import generic
from datetime import datetime
import h5py

# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
config_dict["acq_time_ms"] = nPoints / config_dict["SW_kHz"]
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "generic_echo"
config_dict["date"] = date
config_dict["generic_echo_counter"] += 1
filename = (
    f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
)
# }}}
# {{{set phase cycling
ph1_cyc = r_[0, 1, 2, 3]
ph2_cyc = r_[0]
nPhaseSteps = len(ph1_cyc) * len(ph2_cyc)
# }}}

# {{{check total points
total_pts = nPoints * nPhaseSteps * config_dict["nEchoes"]
assert total_pts < 2**14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
# {{{run echo
data = generic(
    ppg_list=[
        ("phase_reset", 1),
        ("delay_TTL", config_dict['deblank_us']),
        ("pulse_TTL", config_dict['p90_us'], "ph1", ph1_cyc), 
        ("delay", config_dict['tau_us']),
        ("delay_TTL", config_dict['deblank_us']),
        ("pulse_TTL", 2.0 * config_dict['p90_us'], "ph2", ph2_cyc), 
        ("delay", config_dict['deadtime_us']),
        ("acquire", config_dict['acq_time_ms']),
        ("delay", config_dict['repetition_us']),
    ],
    nScans=config_dict["nScans"],
    indirect_idx=0,
    indirect_len=1,
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    acq_time_ms=config_dict["acq_time_ms"],
    SW_kHz=config_dict["SW_kHz"],
    ret_data=None,
)
# }}}
# {{{ chunk and save data
data.chunk(
    "t", ["ph1", "t2"], [len(ph1_cyc), -1]
)
data.setaxis("nScans", r_[0 : config_dict["nScans"]])
data.setaxis("ph1", ph1_cyc / 4)
data.name(config_dict["type"] + "_" + str(config_dict["generic_echo_counter"]))
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
            print("this nodename already exists, so I will call it temp_echo")
            data.name("temp_echo")
            nodename = "temp_echo"
    data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_echo.h5 in the current h5 file"
        )
        if os.path.exists("temp_echo.h5"):
            print("there is a temp_echo.h5 already! -- I'm removing it")
            os.remove("temp_echo.h5")
            data.hdf5_write("temp_echo.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_echo.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", data.name()))
config_dict.write()
# {{{ Image raw data
with figlist_var() as fl:
    data.squeeze()
    fl.next("Raw - time")
    data.set_units("t2", "s")
    fl.image(data)
    data.reorder("t2", first=False)
    data.ft("t2", shift=True)
    data.ft(["ph1"], unitary=True)
    fl.next("FTed data")
    fl.image(data)
# }}}
