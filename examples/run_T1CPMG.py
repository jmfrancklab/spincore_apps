# {{{ note on phase cycling
"""
T1CPMG
======

"""
from pylab import *
from pyspecdata import *
import os, time
from numpy import *
import SpinCore_pp
import h5py
from datetime import datetime
raise RuntimeError("This pulse proram has not been updated.  Before running again, it should be possible to replace a lot of the code below with a call to the function provided by the 'generic' pulse program inside the ppg directory!")

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "T1CPMG"
config_dict["date"] = date
config_dict["cpmg_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{set phase cycling
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0, 2]
    nPhaseSteps = 2
if not phase_cycling:
    ph1_cyc = 0.0
    nPhaseSteps = 1
# }}}
# {{{better tau
marker = 1.0  # 10/10/22 → what is this? → pretty sure the time needed to execute the marker command
pad_start = config_dict["tau_extra_us"] - config_dict["deadtime_us"]
pad_end = (
    config_dict["tau_extra_us"] - config_dict["deblank_us"] - marker
)  # marker + deblank
assert(pad_start > 0), "tau_extra_us must be set to more than deadtime and more than deblank!"
assert (pad_end > 0), "tau_extra_us must be set to more than deadtime and more than deblank!"
twice_tau_echo_us = (  # the period between 180 pulses
    config_dict["tau_extra_us"] * 2 + config_dict["acq_time_ms"] * 1e3
)
# now twice_tau_echo_us/2.0 is τ_echo, so I need to subtract the extra delays
# imposed by the ppg to determine the remaining τ that I need
config_dict["tau_us"] = twice_tau_echo_us / 2.0 - (
    2
    * config_dict["p90_us"]
    / pi  # evolution during pulse -- see eq 6 of coherence paper
    + config_dict["deadtime_us"]  # following 90
    + config_dict["deblank_us"]  # before 180
)
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2 ** 14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
data_length = 2 * nPoints * config_dict['nEchoes'] * nPhaseSteps
# NOTE: Number of segments is nEchoes * nPhaseSteps
vd_kwargs = {
        j:config_dict[j]
        for j in ['krho_cold','krho_hot','T1water_cold','T1water_hot']
        if j in config_dict.keys()
        }
vd_list = SpinCore_pp.vdlist_from_relaxivities(config_dict['concentration'],**vd_kwargs) * 1e6 #convert to microseconds
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
    SpinCore_pp.load(
        [
            ("marker", "start", 1),
            ("phase_reset", 1),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", 2.0 * config_dict["p90_us"], 0),
            ("delay", vd_us),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", config_dict["p90_us"], "ph1", ph1_cyc),
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
    SpinCore_pp.stop_ppg()
    if phase_cycling:
        for x in range(config_dict["nScans"]):
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
    dataPoints = float(shape(data)[0])
    time_axis = linspace(
        0.0,
        config_dict["nEchoes"] * nPhaseSteps * config_dict["acq_time_ms"] * 1e-3,
        dataPoints,
    )
    data = nddata(array(data), "t")
    data.setaxis("t", time_axis).set_units("t", "s")
    if index == 0:
        data_2d = ndshape([len(vd_list), len(time_axis)], ["vd", "t"]).alloc(
            dtype=complex128
        )
        data_2d.setaxis("vd", vd_list * 1e-6).set_units("vd", "s")
        data_2d.setaxis("t", time_axis).set_units("t", "s")
    data_2d["vd", index] = data
SpinCore_pp.stopBoard()
data_2d.name("signal")
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/CPMG")
filename_out = filename + ".h5"
nodename = data_2d.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_T1CPMG")
            data_2d.name("temp_T1CPMG")
            nodename = "temp_T1CPMG"
    data_2d.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        data_2d.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_T1CPMG.h5 in the current h5 file"
        )
        if os.path.exists("temp_T1CPMG.h5"):
            print("there is a temp_T1CPMG.h5 already! -- I'm removing it")
            os.remove("temp_T1CPMG.h5")
            data_2d.hdf5_write("temp_T1CPMG.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_T1CPMG.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", data_2d.name()))
config_dict.write()
fl.show()
