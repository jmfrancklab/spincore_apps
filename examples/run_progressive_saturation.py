"""Run an Enhancement Experiment
================================
Uses power control server so this will need to be running in sync. To do so:
    1. Open Xepr on the EPR computer, connect to spectrometer, and enable XEPR_API.
    2. In a separate terminal on the EPR computer, run the program XEPR_API_server.py and wait for it to tell you 'I am listening'.
    3. On the NMR computer, open a separate terminal in git/inst_notebooks/Instruments and run winpty power_control_server(). When ready to go it will say 'I am listening'.
    4. run this program to collect data
"""
from pyspecdata import *
from numpy import *
import os
import sys
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from Instruments import Bridge12, prologix_connection, gigatronics, power_control
from serial import Serial
import time
from datetime import datetime
from SpinCore_pp.power_helper import gen_powerlist

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "enhancement"
config_dict["date"] = date
config_dict["odnp_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}_{config_dict['odnp_counter']}"
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
# {{{power settings
dB_settings = gen_powerlist(
    config_dict["max_power"], config_dict["power_steps"] + 1, three_down=True
)
print("dB_settings", dB_settings)
print("correspond to powers in Watts", 10 ** (dB_settings / 10.0 - 3))
input("Look ok?")
powers = 1e-3 * 10 ** (dB_settings / 10.0)
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2 ** 14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
# {{{acquire data
with power_control() as p:
    # JF points out it should be possible to save time by removing this (b/c we
    # shut off microwave right away), but AG notes that doing so causes an
    # error.  Therefore, debug the root cause of the error and remove it!
    retval_thermal = p.dip_lock(
        config_dict["uw_dip_center_GHz"] - config_dict["uw_dip_width_GHz"] / 2,
        config_dict["uw_dip_center_GHz"] + config_dict["uw_dip_width_GHz"] / 2,
    )
    p.mw_off()
    time.sleep(16.0)
    echo_data = run_spin_echo(
        nScans=config_dict["thermal_nScans"],
        indirect_idx=0,
        indirect_len=len(powers) + 1,
        ph1_cyc=ph1_cyc,
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        nEchoes=config_dict["nEchoes"],
        p90_us=config_dict["p90_us"],
        repetition_us = config_dict["repetition_us"],
        tau_us=config_dict["tau_us"],
        SW_kHz=config_dict["SW_kHz"],
        ret_data=None,
    )  # assume that the power axis is 1 longer than the
    #                         "powers" array, so that we can also store the
    #                         thermally polarized signal in this array (note
    #                         that powers and other parameters are defined
    #                         globally w/in the script, as this function is not
    #                         designed to be moved outside the module
    power_settings_dBm = np.zeros_like(dB_settings)
    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    for j, this_dB in enumerate(dB_settings):
        logger.debug(
            "SETTING THIS POWER", this_dB, "(", dB_settings[j - 1], powers[j], "W)"
        )
        if j == 0:
            retval = p.dip_lock(
                config_dict["uw_dip_center_GHz"] - config_dict["uw_dip_width_GHz"] / 2,
                config_dict["uw_dip_center_GHz"] + config_dict["uw_dip_width_GHz"] / 2,
            )
        p.set_power(this_dB)
        for k in range(10):
            time.sleep(0.5)
            if p.get_power_setting() >= this_dB:
                break
        if p.get_power_setting() < this_dB:
            raise ValueError("After 10 tries, the power has still not settled")
        time.sleep(5)
        power_settings_dBm[j] = p.get_power_setting()
        run_spin_echo(
            nScans=config_dict["nScans"],
            indirect_idx=j + 1,
            indirect_len=len(powers) + 1,
            ph1_cyc = ph1_cyc,
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            p90_us=config_dict["p90_us"],
            repetition_us=config_dict["repetition_us"],
            tau_us=config_dict["tau_us"],
            SW_kHz=config_dict["SW_kHz"],
            ret_data=echo_data,
        )
#{{{ chunk and save data
if phase_cycling:
    echo_data.chunk("t", ["ph1", "t2"], [len(ph1_cyc), -1])
    echo_data.setaxis("ph1", ph1_cyc / 4)
    if config_dict["nScans"] > 1:
        echo_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    echo_data.reorder(["ph1", "nScans", "t2"])
    echo_data.squeeze()
    echo_data.set_units("t2", "s")
    fl.next("Raw - time")
    fl.image(echo_data.C.mean("nScans"))
    echo_data.reorder("t2", first=False)
    for_plot = echo_data.C
    for_plot.ft('t2',shift=True)
    for_plot.ft(['ph1'], unitary = True)
    fl.next('FTed data')
    fl.image(for_plot.C.mean("nScans")
    )
else:
    if config_dict["nScans"] > 1:
        echo_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    echo_data.rename('t','t2')
    fl.next("Raw - time")
    fl.image(
        echo_data.C.mean("nScans"))
    echo_data.reorder("t2", first=False)
    for_plot = echo_data.C
    for_plot.ft('t2',shift=True)
    fl.next('FTed data')
    fl.image(for_plot)
echo_data.name(config_dict["type"] + "_" + str(config_dict["echo_counter"]))
echo_data.set_prop("postproc_type", "proc_Hahn_echoph")
echo_data.set_prop("acq_params", config_dict.asdict())
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/Echoes")
filename_out = filename + ".h5"
nodename = echo_data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_echo")
            echo_data.name("temp_echo")
            nodename = "temp_echo"
    echo_data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        echo_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_echo.h5 in the current directory"
        )
        if os.path.exists("temp_echo.h5"):
            print("there is a temp_echo.h5 already! -- I'm removing it")
            os.remove("temp_echo.h5")
            echo_data.hdf5_write("temp_echo.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_echo.h5 to the correct name!!"
            )
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", echo_data.name()))
config_dict.write()
fl.show()
