"""
Nutation
========

A standard echo where the 90 time is varied so 
that we are able to see when the signal rotates through 90 to 
180 degrees.
"""
from pyspecdata import *
import os
import SpinCore_pp
from Instruments.XEPR_eth import xepr
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
import h5py

fl = figlist_var()
p90_range_us = linspace(1.0, 10.0, 20, endpoint=False)
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "nutation"
config_dict["date"] = date
config_dict["echo_counter"] += 1
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
# {{{ Edit here to set the actual field
B0 = (
    config_dict["carrierFreq_MHz"] / config_dict["gamma_eff_MHz_G"]
)  # Determine this from Field Sweep
thisB0 = xepr().set_field(B0)
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2 ** 14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
nutation_data = run_spin_echo(
    nScans = config_dict["nScans"],
    indirect_idx = 0,
    indirect_len = len(p90_range_us),
    ph1_cyc = ph1_cyc,
    adcOffset = config_dict["adc_offset"],
    carrierFreq_MHz = config_dict["carrierFreq_MHz"],
    nPoints = nPoints,
    nEchoes = config_dict["nEchoes"],
    p90_us = p90_range_us[0],
    repetition_us = config_dict["repetition_us"],
    tau_us = config_dict["tau_us"],
    SW_kHz = config_dict["SW_kHz"],
    indirect_fields = ("p_90", "index"),
    amplitude =config_dict["amplitude"],
    ret_data = None,
)
mytimes = nutation_data.getaxis("indirect")
mytimes[0]["p_90"] = p90_range_us[0]
for index, val in enumerate(p90_range_us[1:]):
    p90_us = val  # us
    mytimes[index + 1]["p_90"] = p90_us
    run_spin_echo(
        nScans = config_dict["nScans"],
        indirect_idx = index + 1,
        indirect_len = len(p90_range_us),
        ph1_cyc = ph1_cyc,
        adcOffset = config_dict["adc_offset"],
        carrierFreq_MHz = config_dict["carrierFreq_MHz"],
        nPoints = nPoints,
        nEchoes = config_dict["nEchoes"],
        p90_us = p90_us,
        repetition_us = config_dict["repetition_us"],
        tau_us = config_dict["tau_us"],
        SW_kHz = config_dict["SW_kHz"],
        indirect_fields = ("p_90", "index"),
        amplitude =config_dict["amplitude"],
        ret_data = nutation_data,
    )
    mytimes[j+1]["p_90"] = p90_val
if phase_cycling:
    nutation_data.chunk("t", ["ph1", "t2"], [4, -1])
    nutation_data.setaxis("ph1", ph1_cyc)
    if config_dict["nScans"] > 1:
        nutation_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    nutation_data.reorder(["ph1","nScans", "t2"])
    nutation_data.squeeze()
    nutation_data.set_units("t2", "s")
    fl.next("Raw - time")
    fl.image(
        nutation_data.C.mean("nScans"))
    nutation_data.reorder("t2", first=False)
    for_plot = nutation_data.C
    for_plot.ft('t2',shift=True)
    for_plot.ft(['ph1'], unitary = True)
    fl.next('FTed data')
    fl.image(for_plot.C.mean("nScans")
    )
else:
    if config_dict["nScans"] > 1:
        nutation_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    nutation_data.rename("t", "t2")
    fl.next("Raw - time")
    fl.image(
        nutation_data.C.mean("nScans"))
    nutation_data.reorder("t2", first=False)
    for_plot = nutation_data.C
    for_plot.ft('t2',shift=True)
    fl.next('FTed data')
    fl.image(for_plot)
nutation_data.name(config_dict["type"] + "_" + str(config_dict["echo_counter"]))
nutation_data.set_prop("postproc_type", "spincore_nutation_v1")
nutation_data.set_prop("acq_params", config_dict.asdict())
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/nutation")
filename_out = filename + ".h5"
nodename = nutation_data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_nutation")
            nutation_data.name("temp_nutation")
            nodename = "temp_nutation"
        nutation_data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        nutation_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_nutation.h5 in the current directory"
        )
        if os.path.exists("temp_nutation.h5"):
            print("there is a temp_nutation.h5 already! -- I'm removing it")
            os.remove("temp_nutation.h5")
            nutation_data.hdf5_write("temp_nutation.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_nutation.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", nutation_data.name()))
config_dict.write()
fl.show()
