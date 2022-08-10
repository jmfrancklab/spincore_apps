from pyspecdata import *
import os
from . import SpinCore_pp
import socket
import sys
import time
from Instruments.XEPR_eth import xepr

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "MWE"
config_dict["date"] = date
config_dict["echo_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
B0 = (config_dict['carrierFreq_MHz'] / config_dict['gamma_eff_MHz_G'])  # Determine this from Field Sweep
xepr().set_field(B0)
tx_phases = r_[0.0, 90.0, 180.0, 270.0]
nPhaseSteps = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
RX_delay = 120.0
nPoints = 64
tau_adjust = 0.0
tau = RX_delay + config_dict["acq_time_ms"] * 1e3 * 0.5 + tau_adjust
print("TAU DELAY:", tau, "us")
data_length = 2 * nPoints * config_dict["nEchoes"] * nPhaseSteps
num_transients = 100
for index in range(num_transients):
    transient = index + 1
    print("***")
    print("TRANSIENT NUMBER: %d" % (transient))
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
    SpinCore_pp.load(
        [
            ("marker", "start", config_dict["nScans"]),
            ("phase_reset", 1),
            ("pulse", config_dict["p90_us"], 0.0),
            ("delay", tau),
            ("pulse", 2.0 * config_dict["p90_us"], 0.0),
            ("delay", RX_delay),
            ("acquire", acq_time),
            ("delay", config_dict["repetition_us"]),
            ("jumpto", "start"),
        ]
    )
    SpinCore_pp.stop_ppg()
    SpinCore_pp.runBoard()
    raw_data = SpinCore_pp.getData(
        data_length, nPoints, config_dict["nEchoes"], nPhaseSteps, filename
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
        0.0, config_dict["nEchoes"] * nPhaseSteps * acq_time * 1e-3, dataPoints
    )
    data = nddata(array(data), "t")
    data.setaxis("t", time_axis).set_units("t", "s")
    data.name("signal")
    if index == 0:
        transient_data = ndshape(
            [num_transients, len(time_axis)], ["trans_no", "t"]
        ).alloc(dtype=complex128)
        transient_data.setaxis("trans_no", transient)
        transient_data.setaxis("t", time_axis).set_units("t", "s")
    transient_data["trans_no", index] = data
SpinCore_pp.stopBoard()
print("EXITING...\n")
print("\n*** *** ***\n")
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/Echoes")
filename_out = filename + ".h5"
nodename = transient_data.name()
if os.path.exists(filename + ".h5"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp")
            transient_data.name("temp")
            nodename = "temp"
    transient_data.hdf5_write(f"{filename_out}/{nodename}", directory=target_directory)
else:
    try:
        nutation_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp.h5 in the current directory"
        )
        if os.path.exists("temp.h5"):
            print("there is a temp.h5 already! -- I'm removing it")
            os.remove("temp.h5")
            echo_data.hdf5_write("temp.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", transient_data.name()))
print(("Shape of saved data", ndshape(transient_data)))
config_dict.write()
fl.next("raw data")
fl.image(transient_data)
transient_data.ft("t", shift=True)
fl.next("FT raw data")
fl.image(transient_data)
fl.show()
