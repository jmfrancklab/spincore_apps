# {{{ note on phase cycling
"""
FOR PHASE CYCLING: Provide both a phase cycle label (e.g.,
'ph1', 'ph2') as str and an array containing the indices
(i.e., registers) of the phases you which to use that are
specified in the numpy array 'tx_phases'.  Note that
specifying the same phase cycle label will loop the
corresponding phase steps together, regardless of whether
the indices are the same or not.
    e.g.,
    The following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph1',r_[2,3]),
    will provide two transients with phases of the two pulses (p1,p2):
        (0,2)
        (1,3)
    whereas the following:
        ('pulse',2.0,'ph1',r_[0,1]),
        ('delay',1.5),
        ('pulse',2.0,'ph2',r_[2,3]),
    will provide four transients with phases of the two pulses (p1,p2):
        (0,2)
        (0,3)
        (1,2)
        (1,3)
FURTHER: The total number of transients that will be
collected are determined by both nScans (determined when
calling the appropriate marker) and the number of steps
calculated in the phase cycle as shown above.  Thus for
nScans = 1, the SpinCore will trigger 2 times in the first
case and 4 times in the second case.  for nScans = 2, the
SpinCore will trigger 4 times in the first case and 8 times
in the second case.
"""
# }}}
from pylab import *
from pyspecdata import *
from numpy import *
import SpinCore_pp
import time
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
config_dict["cpmg_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
tx_phases = r_[0.0, 90.0, 180.0, 270.0]
marker = 1.0
tau_extra = 1500.0  # us, must be more than deadtime and more than deblank
pad_start = tau_extra - deadtime_us
pad_end = tau_extra - deblank_us * 2  # marker + deblank
twice_tau = (
    deblank_us
    + 2 * p90_us
    + deadtime_us
    + pad_start
    + acq_time_ms * 1e3
    + pad_end
    + marker
)
tau_us = twice_tau / 2.0
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 2
if not phase_cycling:
    nPhaseSteps = 1
data_length = 2 * nPoints * nEchoes * nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
vd_list = r_[5e1, 5.8e5, 9e5, 1.8e6, 2.7e6, 3.6e6, 4.5e6, 5.4e6, 6.4e6, 7.2e6, 10e6]
for index, val in enumerate(vd_list):
    vd_us = val
    print("***")
    print("INDEX %d - VARIABLE DELAY %f" % (index, val))
    print("***")
    SpinCore_pp.configureTX(
        config_dict["adcOffset"],
        config_dict["carrierFreq_MHz"],
        tx_phases,
        config_dict["amplitude"],
        nPoints,
    )
    acq_time_ms = SpinCore_pp.configureRX(
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
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 0),
                ("delay", vd_us),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", config_dict["p90_us"], "ph1", r_[0, 2]),
                ("delay", tau_us),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 1),
                ("delay", config_dict["deadtime_us"]),
                ("delay", pad_start),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", pad_end),
                ("marker", "echo_label", (config_dict["nEchoes"] - 1)),  # 1 us delay
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 1),
                ("delay", config_dict["deadtime_us"]),
                ("delay", pad_start),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", pad_end),
                ("jumpto", "echo_label"),  # 1 us delay
                ("delay", config_dict["repetition_us"]),
                ("jumpto", "start"),
            ]
        )
    if not phase_cycling:
        SpinCore_pp.load(
            [
                ("marker", "start", config_dict["nScans"]),
                ("phase_reset", 1),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
                ("delay", vd_us),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", config_dict["p90_us"], 0.0),
                ("delay", tau_us),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
                ("delay", config_dict["deadtime_us"]),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", pad),
                ("marker", "echo_label", (config_dict["nEchoes"] - 1)),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
                ("delay", config_dict["deadtime_us"]),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", pad),
                ("jumpto", "echo_label"),
                ("delay", config_dict["repetition_us"]),
                ("jumpto", "start"),
            ]
        )
    print("\nSTOPPING PROG BOARD...\n")
    SpinCore_pp.stop_ppg()
    print("\nRUNNING BOARD...\n")
    if phase_cycling:
        for x in range(config_dict["nScans"]):
            print("SCAN NO. %d" % (x + 1))
            SpinCore_pp.runBoard()
    if not phase_cycling:
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
        0.0,
        config_dict["nEchoes"] * nPhaseSteps * config_dict["acq_time_ms"] * 1e-3,
        dataPoints,
    )
    data = nddata(array(data), "t")
    data.setaxis("t", time_axis).set_units("t", "s")
    data.name("signal")
    if index == 0:
        data_2d = ndshape([len(vd_list), len(time_axis)], ["vd", "t"]).alloc(
            dtype=complex128
        )
        data_2d.setaxis("vd", vd_list * 1e-6).set_units("vd", "s")
        data_2d.setaxis("t", time_axis).set_units("t", "s")
    data_2d["vd", index] = data
SpinCore_pp.stopBoard()
print("EXITING...")
print("\n*** *** ***\n")
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/CPMG")
filename_out = filename + ".h5"
nodename = data.name()
if os.path.exists(filename + ".h5"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp")
            data.name("temp")
            nodename = "temp"
    data.hdf5_write(f"{filename_out}/{nodename}", directory=target_directory)
else:
    try:
        data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp.h5 in the current directory"
        )
        if os.path.exists("temp.h5"):
            print("there is a temp.h5 already! -- I'm removing it")
            os.remove("temp.h5")
            data.hdf5_write("temp.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", data.name()))
print(("Shape of saved data", ndshape(data)))
fl.next("raw data")
data_2d *= exp(-1j * data_2d.fromaxis("vd") * clock_correction)
manual_taxis_zero = acq_time * 1e-3 / 2.0  # 2.29e-3
data_2d.setaxis("t", lambda x: x - manual_taxis_zero)
fl.image(data_2d)
data_2d.ft("t", shift=True)
fl.next("FT raw data")
fl.image(data_2d)
fl.show()
