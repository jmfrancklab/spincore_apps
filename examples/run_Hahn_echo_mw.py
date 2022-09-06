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
from Instruments import Bridge12, prologix_connection, gigatronics,power_control
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
# {{{power settings
dB_settings = gen_powerlist(
    config_dict["max_power"], config_dict["power_steps"] + 1, three_down=True
)
print("dB_settings", dB_settings)
print("correspond to powers in Watts", 10 ** (dB_settings / 10.0 - 3))
input("Look ok?")
powers = 1e-3 * 10 ** (dB_settings / 10.0)
# }}}
#{{{phase cycling and checking nPoints
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 4
    Ep_ph1_cyc = r_[0, 1, 2, 3]
if not phase_cycling:
    nPhaseSteps = 1
    Ep_ph1_cyc = r_[0]
total_pts = nPoints * nPhaseSteps
assert total_pts < 2 ** 14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"
    % total_pts
)
# }}}
# {{{check for file
filename_out = filename + ".h5"
if os.path.exists(filename_out):
    raise ValueError(
        "the file %s already exists, either change the chemical name or try incrementing your counter +1" % filename_out
    )
# }}}
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/ODNP")
with power_control() as p:
    # JF points out it should be possible to save time by removing this (b/c we
    # shut off microwave right away), but AG notes that doing so causes an
    # error.  Therefore, debug the root cause of the error and remove it!
    retval_thermal = p.dip_lock(
        config_dict["uw_dip_center_GHz"] - config_dict["uw_dip_width_GHz"] / 2,
        config_dict["uw_dip_center_GHz"] + config_dict["uw_dip_width_GHz"] / 2,
    )
    p.mw_off()
    echo_data = run_spin_echo(
        nScans=config_dict["thermal_nScans"],
        indirect_idx=0,
        indirect_len=len(powers) + 1,
        ph1_cyc=Ep_ph1_cyc,
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        nEchoes=config_dict["nEchoes"],
        p90_us=config_dict["p90_us"],
        repetition=config_dict["repetition_us"],
        tau_us=config_dict["tau_us"],
        SW_kHz=config_dict["SW_kHz"],
        output_name=filename,
        ret_data=None,
    )  # assume that the power axis is 1 longer than the
    #                         "powers" array, so that we can also store the
    #                         thermally polarized signal in this array (note
    #                         that powers and other parameters are defined
    #                         globally w/in the script, as this function is not
    #                         designed to be moved outside the module
    echo_data = echo_data['nScans',-1:]
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
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            p90_us=config_dict["p90_us"],
            repetition=config_dict["repetition_us"],
            tau_us=config_dict["tau_us"],
            SW_kHz=config_dict["SW_kHz"],
            output_name=filename,
            ret_data=echo_data,
        )
echo_data.set_prop("postproc_type", "spincore_ODNP_v3")
echo_data.set_prop("acq_params", config_dict.asdict())
echo_data.name(config_dict["type"])
if phase_cycling:
    echo_data.chunk("t", ["ph1", "t2"], [len(Ep_ph1_cyc), -1])
    echo_data.setaxis("ph1", Ep_ph1_cyc / 4)
    echo_data.reorder(['ph1','indirect','t2'])
echo_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
# }}}
# }}}
fl.next("raw data_array")
fl.image(echo_data.C.setaxis("indirect", "#").set_units("indirect", "scan #"))
fl.next("abs raw data_array")
fl.image(abs(echo_data).C.setaxis("indirect", "#").set_units("indirect", "scan #"))
if phase_cycling:
    echo_data.ft("t2", shift=True)
    echo_data.ft(["ph1"])
else:
    echo_data.ft("t")
fl.next("raw data_array - ft")
fl.image(echo_data.C.setaxis("indirect", "#"))
fl.next("abs raw data_array - ft")
fl.image(abs(echo_data.C.setaxis("indirect", "#")))
nodename = echo_data.name()
try:
    echo_data.hdf5_write(f"{filename_out}",directory = target_directory)
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
logger.info("FILE SAVED")
logger.debug(strm("Name of saved enhancement data", echo_data.name()))
logger.debug("shape of saved enhancement data", ndshape(echo_data))
config_dict.write()
fl.show()
