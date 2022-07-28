from pyspecdata import *
import os
from . import SpinCore_pp
import socket
import sys
import time

fl = figlist_var()
# {{{ Verify arguments compatible with board
def verifyParams():
    if nPoints > 16 * 1024 or nPoints < 1:
        print("ERROR: MAXIMUM NUMBER OF POINTS IS 16384.")
        print("EXITING.")
    else:
        print("VERIFIED NUMBER OF POINTS.")
    if nScans < 1:
        print("ERROR: THERE MUST BE AT LEAST 1 SCAN.")
        print("EXITING.")
    else:
        print("VERIFIED NUMBER OF SCANS.")
    if p90 < 0.065:
        print("ERROR: PULSE TIME TOO SMALL.")
        print("EXITING.")
    else:
        print("VERIFIED PULSE TIME.")
    if tau < 0.065:
        print("ERROR: DELAY TIME TOO SMALL.")
        print("EXITING.")
    else:
        print("VERIFIED DELAY TIME.")
    return


# }}}
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
# {{{ for setting EPR magnet
def API_sender(value):
    IP = "jmfrancklab-bruker.syr.edu"
    if len(sys.argv) > 1:
        IP = sys.argv[1]
    PORT = 6001
    print("target IP:", IP)
    print("target port:", PORT)
    MESSAGE = str(value)
    print("SETTING FIELD TO...", MESSAGE)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Internet  # TCP
    sock.connect((IP, PORT))
    sock.send(MESSAGE)
    sock.close()
    print("FIELD SET TO...", MESSAGE)
    time.sleep(5)
    return


# }}}
set_field = False
if set_field:
    B0 = 3409.3  # Determine this from Field Sweep
    API_sender(B0)
tx_phases = r_[0.0, 90.0, 180.0, 270.0]
nPhaseSteps = 1
# NOTE: Number of segments is nEchoes * nPhaseSteps
RX_delay = 120.0
nPoints = 64
tau_adjust = 0.0
tau = RX_delay + acq_time * 1e3 * 0.5 + tau_adjust
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
    transient_data.hdf5_write(filename + ".h5", directory=target_directory)
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
