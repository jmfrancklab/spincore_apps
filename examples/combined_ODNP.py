"""Automated Combined DNP with Log
==================================
This needs to be run in sync with the power control server. To do so:
    1. Open Xepr on EPR computer, connect to spectrometer, enable XEPR_API and then in new terminal, run XEPR_API_server.py. When this is ready to go you will see it say "I am listening".
    2. Open new terminal on NMR computer, move into git/inst_notebooks/Instruments and run wipty power_control_server.py. When this is ready to go it will read "I am listening"
Once the power control server is up and ready to go you may run this script to collect the enhancement data as well as a series of IRs at increasing power collected in sync with a time log.
"""
import numpy as np
from numpy import r_
from pyspecdata import *
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
from pyspecdata import strm
import os, sys, time
import h5py
import SpinCore_pp
from SpinCore_pp.power_helper import gen_powerlist
from SpinCore_pp.ppg import run_spin_echo, run_IR
from Instruments import power_control
from datetime import datetime

logger = init_logging(level="debug")
fl = figlist_var()
thermal_scans = 4
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "ODNP"
config_dict["date"] = date
config_dict["odnp_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}_{config_dict['odnp_counter']}"
filename_out = filename + ".h5"
# }}}
# {{{set phase cycling
phase_cycling = True
if phase_cycling:
    Ep_ph1_cyc = r_[0, 1, 2, 3]
    Ep_nPhaseSteps = 4
    IR_ph1_cyc = r_[0, 2]
    IR_ph2_cyc = r_[0, 2]
    IR_nPhaseSteps = 4
if not phase_cycling:
    Ep_ph1_cyc = 0.0
    Ep_nPhaseSteps = 1
    IR_ph1_cyc = 0.0
    IR_ph2_cyc = 0.0
    IR_nPhaseSteps = 2
#}}}
# {{{Make VD list based on concentration and FIR repetition delay as defined by Weiss
vd_kwargs = {
    j: config_dict[j]
    for j in ["krho_cold", "krho_hot", "T1water_cold", "T1water_hot"]
    if j in config_dict.keys()
}
vd_list_us = (
    SpinCore_pp.vdlist_from_relaxivities(config_dict["concentration"], **vd_kwargs)
    * 1e6
)  # convert to microseconds
FIR_rep = 2*(1.0/(config_dict['concentration']*config_dict['krho_hot']+1.0/config_dict['T1water_hot']))*1e6
config_dict['FIR_rep'] = FIR_rep
# }}}
# {{{Power settings
dB_settings = gen_powerlist(
    config_dict["max_power"], config_dict["power_steps"] + 1, three_down=True
)
T1_powers_dB = gen_powerlist(
    config_dict["max_power"], config_dict["num_T1s"], three_down=False
)
T1_node_names = ["FIR_%ddBm" % j for j in T1_powers_dB]
logger.info("dB_settings", dB_settings)
logger.info("correspond to powers in Watts", 10 ** (dB_settings / 10.0 - 3))
logger.info("T1_powers_dB", T1_powers_dB)
logger.info("correspond to powers in Watts", 10 ** (T1_powers_dB / 10.0 - 3))
myinput = input("Look ok?")
if myinput.lower().startswith("n"):
    raise ValueError("you said no!!!")
powers = 1e-3 * 10 ** (dB_settings / 10.0)
# }}}
#{{{check total points
total_points = len(Ep_ph1_cyc) * nPoints
assert total_points < 2 ** 14, (
    "For Ep: You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % total_pts
)
total_pts = len(IR_ph2_cyc) * len(IR_ph1_cyc) * nPoints
assert total_pts < 2 ** 14, (
    "For IR: You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % total_pts
)
# }}}
# {{{ check for file
if os.path.exists(filename_out):
    raise ValueError(
        "the file %s already exists, so I'm not going to let you proceed!"
        % filename_out
    )
input(
    "B12 needs to be unplugged and turned off for the thermal! Don't have the power server running just yet"
)
# }}}
# {{{Collect Thermals - serves as a control to compare the thermal of Ep to ensure no microwaves were leaking
control_thermal = run_spin_echo(
    nScans=config_dict["thermal_nScans"],
    indirect_idx=0,
    indirect_len=len(powers) + 1,
    ph1_cyc=Ep_ph1_cyc,
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    nEchoes=config_dict["nEchoes"],
    p90_us=config_dict["p90_us"],
    repetition_us=config_dict["repetition_us"],
    tau_us=config_dict["tau_us"],
    SW_kHz=config_dict["SW_kHz"],
    indirect_fields=("start_times", "stop_times"),
    ret_data=None,
)  # assume that the power axis is 1 longer than the
#                         "powers" array, so that we can also store the
#                         thermally polarized signal in this array (note
#                         that powers and other parameters are defined
#                         globally w/in the script, as this function is not
#                         designed to be moved outside the module
if phase_cycling:
    control_thermal.chunk("t", ["ph1", "t2"], [len(Ep_ph1_cyc), -1])
    control_thermal.setaxis("ph1", Ep_ph1_cyc / 4)
    if config_dict["nScans"] > 1:
        control_thermal.setaxis("nScans", r_[0 : config_dict["nScans"]])
    control_thermal.reorder(["ph1", "nScans", "t2"])
else:
    if config_dict["nScans"] > 1:
        control_thermal.setaxis("nScans", r_[0 : config_dict["nScans"]])
control_thermal.name("control_thermal")
control_thermal.set_prop("postproc_type", "spincore_ODNP_v3")
control_thermal.set_prop("acq_params", config_dict.asdict())
control_thermal.name("control_thermal")
filename_out = filename + ".h5"
nodename = control_thermal.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_control_thermal")
            control_thermal.name("temp_control_thermal")
            nodename = "temp_control_thermal"
    control_thermal.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        control_thermal_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_control_thermal.h5 in the current directory"
        )
        if os.path.exists("temp_control_thermal.h5"):
            print("there is a temp_control_thermal.h5 already! -- I'm removing it")
            os.remove("temp_control_thermal.h5")
            control_thermal.hdf5_write("temp_control_thermal.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_control_thermal.h5 to the correct name!!"
            )
logger.info("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
logger.debug(strm("Name of saved data", control_thermal.name()))
# }}}
# {{{IR at no power
#   this is outside the log, so to deal with this during processing, just check
#   if the start and stop time are outside the log (greater than last time of
#   the time axis, or smaller than the first)
ini_time = time.time()
vd_data = None
for vd_idx, vd in enumerate(vd_list_us):
    vd_data = run_IR(
        nPoints=nPoints,
        nEchoes=config_dict["nEchoes"],
        indirect_idx=vd_idx,
        indirect_len=len(vd_list_us),
        vd=vd,
        nScans=config_dict["thermal_nScans"],
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        p90_us=config_dict["p90_us"],
        tau_us=config_dict["tau_us"],
        repetition_us=FIR_rep,
        ph1_cyc=IR_ph1_cyc,
        ph2_cyc=IR_ph2_cyc,
        SW_kHz=config_dict["SW_kHz"],
        ret_data=vd_data,
    )
vd_data.rename("indirect", "vd")
vd_data.setaxis("vd", vd_list_us * 1e-6).set_units("vd", "s")
if phase_cycling:
    vd_data.chunk("t", ["ph2", "ph1", "t2"], [len(IR_ph1_cyc), len(IR_ph2_cyc), -1])
    vd_data.setaxis("ph1", IR_ph1_cyc / 4)
    vd_data.setaxis("ph2", IR_ph2_cyc / 4)
vd_data.setaxis("nScans", r_[0 : config_dict["thermal_nScans"]])
vd_data.name("FIR_noPower")
vd_data.set_prop("stop_time", time.time())
vd_data.set_prop("start_time", ini_time)
vd_data.set_prop("acq_params", config_dict.asdict())
vd_data.set_prop("postproc_type", "spincore_IR_v1")
nodename = vd_data.name()
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp_FIR_noPower")
            vd_data.name("temp_FIR_noPower")
            nodename = "temp_FIR_noPower"
    vd_data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        vd_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_FIR_noPower.h5 in the current directory"
        )
        if os.path.exists("temp_FIR_noPower.h5"):
            print("there is a temp_FIR_noPower.h5 already! -- I'm removing it")
            os.remove("temp_FIR_noPower.h5")
            vd_data.hdf5_write("temp_FIR_noPower.h5")
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_FIR_noPower.h5 to the correct name!!"
            )
logger.debug("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
logger.debug(strm("Name of saved data", vd_data.name()))
# }}}
# {{{run enhancement
input("Now plug the B12 back in and start up the power_server so we can continue!")
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
    p.start_log()
    for j in range(thermal_scans):
        DNP_ini_time = time.time()
        if j == 0:
            DNP_data = run_spin_echo(
                nScans=config_dict["nScans"],
                indirect_idx=j,
                indirect_len=len(powers) + thermal_scans,
                ph1_cyc=Ep_ph1_cyc,
                adcOffset=config_dict["adc_offset"],
                carrierFreq_MHz=config_dict["carrierFreq_MHz"],
                nPoints=nPoints,
                nEchoes=config_dict["nEchoes"],
                ph1_cyc=Ep_ph1_cyc,
                p90_us=config_dict["p90_us"],
                repetition_us=config_dict["repetition_us"],
                tau_us=config_dict["tau_us"],
                SW_kHz=config_dict["SW_kHz"],
                indirect_fields=("start_times", "stop_times"),
                ret_data=None,
            )  
            DNP_thermal_done = time.time()
            time_axis_coords = DNP_data.getaxis("indirect")
        else:
            DNP_data = run_spin_echo(
                nScans=parser_dict['nScans'],
                indirect_idx=j,
                indirect_len=len(powers) + thermal_scans,
                adcOffset=parser_dict['adc_offset'],
                carrierFreq_MHz=parser_dict['carrierFreq_MHz'],
                nPoints=nPoints,
                nEchoes=parser_dict['nEchoes'],
                ph1_cyc=Ep_ph1_cyc,
                p90_us=parser_dict['p90_us'],
                repetition_us=parser_dict['repetition_us'],
                tau_us=parser_dict['tau_us'],
                SW_kHz=parser_dict['SW_kHz'],
                indirect_fields=("start_times", "stop_times"),
                ret_data=DNP_data,
            )
        DNP_thermal_done = time.time()
        time_axis_coords[j]["start_times"] = DNP_ini_time
        time_axis_coords[j]["stop_times"] = DNP_thermal_done
    power_settings_dBm = np.zeros_like(dB_settings)
    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    for j, this_dB in enumerate(dB_settings):
        logger.debug(
            "SETTING THIS POWER", this_dB, "(", dB_settings[j - 1], powers[j], "W)"
        )
        if j == 0:
            retval = p.dip_lock(
                config_dict['uw_dip_center_GHz'] - config_dict['uw_dip_width_GHz'] / 2,
                config_dict['uw_dip_center_GHz'] + config_dict['uw_dip_width_GHz'] / 2,
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
        time_axis_coords[j + thermal_scans]["start_times"] = time.time()
        run_spin_echo(
            nScans=config_dict["nScans"],
            indirect_idx=j + thermal_scans,
            indirect_len=len(powers) + thermal_scans,
            ph1_cyc=Ep_ph1_cyc,
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            p90_us=config_dict["p90_us"],
            repetition_us=config_dict["repetition_us"],
            tau_us=config_dict["tau_us"],
            SW_kHz=config_dict["SW_kHz"],
            ret_data=DNP_data,
        )
        time_axis_coords[j + thermal_scans]["stop_times"] = time.time()
    DNP_data.set_prop("stop_time", time.time())
    DNP_data.set_prop("postproc_type", "spincore_ODNP_v4")
    DNP_data.set_prop("acq_params", config_dict.asdict())
    DNP_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    if phase_cycling:
        DNP_data.chunk("t", ["ph1", "t2"], [len(Ep_ph1_cyc), -1])
        DNP_data.setaxis("ph1", Ep_ph1_cyc / 4)
        DNP_data.reorder(["ph1", "nScans", "t2"])
    DNP_data.name(config_dict["type"])
    nodename = DNP_data.name()
    try:
        DNP_data.hdf5_write(f"{filename_out}", directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_ODNP.h5 in the current h5 file"
        )
        if os.path.exists("temp_ODNP.h5"):
            print("there is a temp_ODNP.h5 already! -- I'm removing it")
            os.remove("temp_ODNP.h5")
            DNP_data.hdf5_write("temp_ODNP.h5", directory=target_directory)
            print(
                "if I got this far, that probably worked -- be sure to move/rename temp_ODNP.h5 to the correct name!!"
    logger.info("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
    logger.debug(strm("Name of saved data", echo_data.name()))
    # }}}
    # {{{run IR
    for j, this_dB in enumerate(T1_powers_dB):
        p.set_power(this_dB)
        for k in range(10):
            time.sleep(0.5)
            # JF notes that the following works for powers going up, but not
            # for powers going down -- I don't think this has been a problem to
            # date, and would rather not potentially break a working
            # implementation, but we should PR and fix this in the future.
            # (Just say whether we're closer to the newer setting or the older
            # setting.)
            if p.get_power_setting() >= this_dB:
                break
        if p.get_power_setting() < this_dB:
            raise ValueError("After 10 tries, the power has still not settled")
        time.sleep(5)
        meter_power = p.get_power_setting()
        ini_time = time.time()
        vd_data = None
        for vd_idx, vd in enumerate(vd_list_us):
            vd_data = run_IR(
                nPoints=nPoints,
                nEchoes=config_dict["nEchoes"],
                indirect_idx=vd_idx,
                indirect_len=len(vd_list_us),
                ph1_cyc=IR_ph1_cyc,
                ph2_cyc=IR_ph2_cyc,
                vd=vd,
                nScans=config_dict["nScans"],
                adcOffset=config_dict["adc_offset"],
                carrierFreq_MHz=config_dict["carrierFreq_MHz"],
                p90_us=config_dict["p90_us"],
                tau_us=config_dict["tau_us"],
                repetition_us=FIR_rep,
                SW_kHz=config_dict["SW_kHz"],
                ret_data=vd_data,
            )
        vd_data.rename("indirect", "vd")
        vd_data.setaxis("vd", vd_list_us * 1e-6).set_units("vd", "s")
        vd_data.set_prop("start_time", ini_time)
        vd_data.set_prop("stop_time", time.time())
        vd_data.set_prop("acq_params", config_dict.asdict())
        vd_data.set_prop("postproc_type", "spincore_IR_v1")
        vd_data.name(T1_node_names[j])
        if phase_cycling:
            vd_data.chunk("t", ["ph2", "ph1", "t2"], [len(IR_ph2_cyc), len(IR_ph1_cyc), -1])
            vd_data.setaxis("ph1", IR_ph1_cyc / 4)
            vd_data.setaxis("ph2", IR_ph2_cyc / 4)
        vd_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
        nodename = vd_data.name()
        if os.path.exists(os.path.normpath(os.path.join(target_directory, f"{filename_out}/{nodename}")):
            if nodename in fp.keys():
                print("this nodename already exists, so I will call it temp_%d" % j)
                vd_data.name("temp_%d" % this_dB)
                nodename = "temp_%d" % this_dB
                vd_data.hdf5_write(f"{filename_out}", directory=target_directory)
            else:
                vd_data.hdf5_write(f"{filename_out}", directory=target_directory)
        print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
        print(("Name of saved data", vd_data.name()))
    final_frq = p.dip_lock(
        config_dict["uw_dip_center_GHz"] - config_dict["uw_dip_width_GHz"] / 2,
        config_dict["uw_dip_center_GHz"] + config_dict["uw_dip_width_GHz"] / 2,
    )
    this_log = p.stop_log()
# }}}
config_dict.write()
with h5py.File(os.path.join(target_directory, f"{filename_out}"), "a") as f:
    log_grp = f.create_group("log")
    hdf_save_dict_to_group(log_grp, this_log.__getstate__())
