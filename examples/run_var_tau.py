from pyspecdata import *
import os
import sys
import SpinCore_pp
from datetime import datetime

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "echo"
config_dict["date"] = date
config_dict["echo_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
phase_cycling = True
coherence_pathway = [("ph1", 1), ("ph2", -2)]
if phase_cycling:
    nPhaseSteps = 8
if not phase_cycling:
    nPhaseSteps = 1
# {{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
# }}}
tau_adjust_range = r_[1e3:30e3:1000]
tau_axis = tau
if phase_cycling:
    config_dict["nPhaseSteps"] = nPhaseSteps
# }}}
tx_phases = r_[0.0, 90.0, 180.0, 270.0]
print(("ACQUISITION TIME:", acq_time, "ms"))
data_length = 2 * nPoints * config_dict["nEchoes"] * nPhaseSteps
for index, val in enumerate(tau_adjust_range):
    tau_adjust = val  # us
    # calculate tau each time through
    tau = (
        config_dict["deadtime_us"]
        + config_dict["acq_time_ms"] * 1e3 * (1.0 / 8.0)
        + tau_adjust
    )
    print("***")
    print("INDEX %d - TAU %f" % (index, tau))
    print("***")
    SpinCore_pp.configureTX(
        config_dict["adcOffset"],
        config_dict["carrierFreq_MHz"],
        tx_phases,
        config_dict["amplitude"],
        nPoints,
    )
    acq_time = SpinCore_pp.configureRX(
        config_dict["SW_kHz"],
        nPoints,
        config_dict["nScans"],
        config_dict["nEchoes"],
        nPhaseSteps,
    )  # ms
    SpinCore_pp.init_ppg()
    if phase_cycling:
        SpinCore_pp.load(
            [
                ("marker", "start", 1),
                ("phase_reset", 1),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", config_dict["p90_us"], "ph1", r_[0, 1, 2, 3]),
                ("delay", tau),
                ("delay_TTL", config_dict["deblank"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], "ph2", r_[0, 2]),
                ("delay", config_dict["deadtime"]),
                ("acquire", acq_time),
                ("delay", config_dict["repetition_us"]),
                ("jumpto", "start"),
            ]
        )
    if not phase_cycling:
        SpinCore_pp.load(
            [
                ("marker", "start", config_dict["nScans"]),
                ("phase_reset", 1),
                ("delay_TTL", config_dict["deblank"]),
                ("pulse_TTL", config_dict["p90_us"], 0.0),
                ("delay", tau),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
                ("delay", config_dict["deadtime_us"]),
                ("acquire", acq_time),
                ("delay", config_dict["repetition_us"]),
                ("jumpto", "start"),
            ]
        )
    SpinCore_pp.stop_ppg()
    if phase_cycling:
        for x in range(config_dict["nScans"]):
            print("SCAN NO. %d" % (x + 1))
            SpinCore_pp.runBoard()
    if not phase_cycling:
        SpinCore_pp.runBoard()
    raw_data = SpinCore_pp.getData(
        data_length,
        nPoints,
        config_dict["nEchoes"],
        config_dict["nPhaseSteps"],
        filename,
    )
    raw_data.astype(float)
    data = []
    # according to JF, this commented out line
    # should work same as line below and be more effic
    # data = raw_data.view(complex128)
    data[::] = complex128(raw_data[0::2] + 1j * raw_data[1::2])
    print("COMPLEX DATA ARRAY LENGTH:", shape(data)[0])
    print("RAW DATA ARRAY LENGTH:", shape(raw_data)[0])
    dataPoints = float(shape(data)[0])
    time_axis = linspace(
        0.0,
        config_dict["nEchoes"] * config_dict["nPhaseSteps"] * acq_time * 1e-3,
        dataPoints,
    )
    data = nddata(array(data), "t")
    data.setaxis("t", time_axis).set_units("t", "s")
    data.name("signal")
    if index == 0:
        var_tau_data = ndshape(
            [len(tau_adjust_range), len(time_axis)], ["tau", "t"]
        ).alloc(dtype=complex128)
        var_tau_data.setaxis("tau", tau_axis * 1e-6).set_units("tau", "s")
        var_tau_data.setaxis("t", time_axis).set_units("t", "s")
    var_tau_data["tau", index] = data
SpinCore_pp.stopBoard()
print("EXITING...\n")
print("\n*** *** ***\n")
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/var_tau")
filename_out = filename + ".h5"
nodename = var_tau_data.name()
if os.path.exists(filename + ".h5"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp")
            var_tau_data.name("temp")
            nodename = "temp"
    var_tau_data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        var_tau_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp.h5 in the current directory"
        )
        if os.path.exists("temp.h5"):
            print("there is a temp.h5 -- I'm removing it")
            os.remove("temp.h5")
        var_tau_data.hdf5_write("temp.h5")
        print(
            "if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!"
        )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", var_tau_data.name()))
print(("Shape of saved data", ndshape(var_tau_data)))
config_dict.write()
fl.next("raw data")
fl.image(var_tau_data)
var_tau_data.ft("t", shift=True)
fl.next("FT raw data")
fl.image(var_tau_data)
fl.show()
