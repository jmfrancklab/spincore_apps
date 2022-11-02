"""
Varied Tau Experiment
=====================

A standard echo that is repeated varying the echo time between pulses. The tau value is adjusted 
to ensure a symmetric echo.
"""
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
import h5py

fl = figlist_var()
tau_adjust_range = r_[1e3:30e3:1000]
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "Var_Tau"
config_dict["date"] = date
config_dict["echo_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{set phase cycling
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
# {{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2 ** 14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
tau = config_dict['deadtime'] + config_dict['acq_time_ms']*1e3*(1./8.) +tau_adjust_range
tau_axis = tau
# }}}
# {{{ acquire varied tau data
var_tau_data = run_spin_echo(
    nScans = config_dict["nScans"],
    indirect_idx = 0,
    indirect_len = len(tau_adjust_range),
    ph1_cyc = ph1_cyc,
    ph2_cyc = ph2_cyc,
    adcOffset = config_dict["adc_offset"],
    carrierFreq_MHz = config_dict["carrierFreq_MHz"],
    nPoints = nPoints,
    nEchoes = config_dict["nEchoes"],
    p90_us = config_dict["p90_us"],
    repetition_us = config_dict["repetition_us"],
    tau_us = tau,
    SW_kHz = config_dict["SW_kHz"],
    indirect_fields = ("tau_adjust","tau"),
    ret_data = None,
)
mytau_axis = var_tau_data.getaxis("indirect")
mytau_axis[0]["tau_adjust"] = tau_adjust
mytaus_axis[0]["tau"] = tau
# {{{run varied tau
for tau_idx, val in enumerate(tau_adjust_range[1:]):
    tau_adjust = val  # us
    # calculate tau each time through
    tau = (
        config_dict["deadtime_us"]
        + config_dict["acq_time_ms"] * 1e3 * (1.0 / 8.0)
        + tau_adjust
    )
    var_tau_data = run_spin_echo(
            nScans = config_dict["nScans"],
            indirect_idx = tau_idx+1,
            indirect_len = len(tau_adjust_range),
            ph1_cyc = ph1_cyc,
            ph2_cyc = ph2_cyc,
            adcOffset = config_dict["adc_offset"],
            carrierFreq_MHz = config_dict["carrierFreq_MHz"],
            nPoints = nPoints,
            nEchoes = config_dict["nEchoes"],
            p90_us = config_dict["p90_us"],
            repetition_us = config_dict["repetition_us"],
            tau_us = tau,
            SW_kHz = config_dict["SW_kHz"],
            indirect_fields = ("tau_adjust","tau"),
            ret_data = var_tau_data,
        )
        mytau_axis = var_tau_data.getaxis("indirect")
        mytau_axis[tau_idx+1]["tau_adjust"] = tau_adjust
        mytaus_axis[tau_idx+1]["tau"] = tau
if phase_cycling:
    var_tau_data.chunk("t", ["ph1", "ph2","t2"], [len(ph1_cyc),len(ph2_cyc) -1])
    var_tau_data.setaxis("ph1", ph1_cyc)
    var_tau_data.setaxis("ph2", ph2_cyc)
    if config_dict["nScans"] > 1:
        var_tau_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    var_tau_data.reorder(["ph1", "ph2", "nScans", "t2"])
    var_tau_data.squeeze()
    var_tau_data.set_units("t2", "s")
    fl.next("Raw - time")
    fl.image(
        var_tau_data.C.mean("nScans"))
    var_tau_data.reorder("t2", first=False)
    for_plot = var_tau_data.C
    for_plot.ft('t2',shift=True)
    for_plot.ft(['ph1', 'ph2'], unitary = True)
    fl.next('FTed data')
    fl.image(for_plot.C.mean("nScans")
    )
else:
    if config_dict["nScans"] > 1:
        var_tau_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    var_tau_data.rename("t", "t2")
    fl.next("Raw - time")
    fl.image(
        var_tau_data.C.mean("nScans"))
    var_tau_data.reorder("t2", first=False)
    for_plot = var_tau_data.C
    for_plot.ft('t2',shift=True)
    fl.next('FTed data')
    fl.image(for_plot)
var_tau_data.name(config_dict["type"] + "_" + str(config_dict["echo_counter"]))
var_tau_data.set_prop("postproc_type","SpinCore_var_tau_v1") #still needs to be added to load_Data
var_tau_data.set_prop("acq_params", config_dict.asdict())
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/var_tau")
filename_out = filename + ".h5"
nodename = var_tau_data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_var_tau")
            var_tau_data.name("temp_var_tau")
            nodename = "temp_var_tau"
        var_tau_data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        var_tau_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_var_tau.h5 in the current directory"
        )
        if os.path.exists("temp_var_tau.h5"):
            print("there is a temp_var_tau.h5 already! -- I'm removing it")
            os.remove("temp_var_tau.h5")
            var_tau_data.hdf5_write("temp_var_tau.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_var_tau.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", var_tau_data.name()))
config_dict.write()
fl.show()
