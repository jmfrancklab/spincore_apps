"""Automated Combined DNP with Log
==================================
This needs to be run in sync with the power control server. To do so:
    1. Open Xepr on EPR computer, connect to spectrometer, enable XEPR_API and then in new terminal, run XEPR_API_server.py which allows the bruker electromagnet to communicate with the ppg. When this is ready to go you will see the terminal say "I am listening".
    2. The experiment starts with the B12 off. It collects your IR at no power along with a series of "control" thermals. These can be used for diagnosing issues with the enhancement thermal, for example, if microwaves are leaking into the cavity.
    3. You will then be prompted to turn the B12 and the power control server on. To turn the power control server on, open a new terminal and type "FLInst server",
        wait until you see "I am listening" before continuing with the experiment.
    At the end of the experiment you will have a series of FIR experiments, a progressive power saturation dataset, and a log of the power over time saved as nodes in an h5 file.
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

final_log = []

logger = init_logging(level="debug")
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/ODNP")
fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
thermal_scans = config_dict['thermal_nscans'] 
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "ODNP"
config_dict["date"] = date
config_dict["odnp_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}_{config_dict['odnp_counter']}.h5"
# }}}
# {{{set phase cycling
phase_cycling = True
if phase_cycling:
    Ep_ph1_cyc = r_[0, 1, 2, 3]
    IR_ph1_cyc = r_[0, 2]
    IR_ph2_cyc = r_[0, 2]
if not phase_cycling:
    Ep_ph1_cyc = 0.0
    IR_ph1_cyc = 0.0
    IR_ph2_cyc = 0.0
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
T1_node_names = ["FIR_%0.1fdBm" % j for j in T1_powers_dB]
logger.info("dB_settings", dB_settings)
logger.info("correspond to powers in Watts", 10 ** (dB_settings / 10.0 - 3))
logger.info("T1_powers_dB", T1_powers_dB)
logger.info("correspond to powers in Watts", 10 ** (T1_powers_dB / 10.0 - 3))
myinput = input("Look ok?")
if myinput.lower().startswith("n"):
    raise ValueError("you said no!!!")
powers = 1e-3 * 10 ** (dB_settings / 10.0)
# }}}
# {{{ these change if we change the way the data is saved
IR_postproc = "spincore_IR_v1" # note that you have changed the way the data is saved, and so this should change likewise!!!!
Ep_postproc = "spincore_ODNP_v3"
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
if os.path.exists(filename):
    raise ValueError(
        "the file %s already exists, so I'm not going to let you proceed!"
        % filename
    )
input(
    "B12 needs to be unplugged and turned off for the thermal! Don't have the power server running just yet"
)
# }}}
# {{{Collect Thermals - serves as a control to compare the thermal of Ep to ensure no microwaves were leaking
# call A to run spin echo
control_thermal = run_spin_echo(
    nScans=config_dict["thermal_nScans"],
    indirect_idx=0,
    indirect_len=1,
    ph1_cyc=Ep_ph1_cyc,
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    nEchoes=config_dict["nEchoes"],
    p90_us=config_dict["p90_us"],
    repetition_us=config_dict["repetition_us"],
    tau_us=config_dict["tau_us"],
    SW_kHz=config_dict["SW_kHz"],
    indirect_fields = ("start_times", "stop_times"),
    ret_data=None,
) 
if config_dict["thermal_nScans"] > 1:
    control_thermal.setaxis("nScans", r_[0 : config_dict["thermal_nScans"]])
if phase_cycling:
    control_thermal.chunk("t", ["ph1", "t2"], [len(Ep_ph1_cyc), -1])
    control_thermal.setaxis("ph1", Ep_ph1_cyc / 4)
    control_thermal.reorder(["ph1", "nScans", "t2"])
control_thermal.name("control_thermal")
control_thermal.set_prop("postproc_type", Ep_postproc)
control_thermal.set_prop("acq_params", config_dict.asdict())
control_thermal.name("control_thermal")
nodename = control_thermal.name()
# {{{ on first write, if we can't access the directory, write to a temp file
try:
    control_thermal.hdf5_write(filename, directory=target_directory)
except:
    final_log.append(
        f"I had problems writing to the correct file {filename}, so I'm going to try to save your file to temp_ctrl.h5 in the current directory"
    )
    if os.path.exists("temp_ctrl.h5"):
        final_log.append("There is already a temp_ctrl.h5 -- I'm removing it")
        os.remove("temp_ctrl.h5")
        target_directory = os.path.getcwd()
        filename = "temp_ctrl.h5"
        DNP_data.hdf5_write(f'{filename}', directory=target_directory)
        final_log.append("change the name accordingly once this is done running!")
# }}}
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
    # call A to run_IR
    vd_data = run_IR(
        nPoints=nPoints,
        nEchoes=config_dict["nEchoes"],
        indirect_idx=vd_idx,
        indirect_len=len(vd_list_us),
        ph1_cyc=IR_ph1_cyc,
        ph2_cyc=IR_ph2_cyc,
        vd=vd,
        nScans=config_dict["thermal_nScans"],
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
if phase_cycling:
    vd_data.chunk("t", ["ph2", "ph1", "t2"], [len(IR_ph1_cyc), len(IR_ph2_cyc), -1])
    vd_data.setaxis("ph1", IR_ph1_cyc / 4)
    vd_data.setaxis("ph2", IR_ph2_cyc / 4)
vd_data.setaxis("nScans", r_[0 : config_dict["thermal_nScans"]])
vd_data.name("FIR_noPower")
vd_data.set_prop("stop_time", time.time())
vd_data.set_prop("start_time", ini_time)
vd_data.set_prop("acq_params", config_dict.asdict())
vd_data.set_prop("postproc_type", IR_postproc)
nodename = vd_data.name()
# {{{ again, implement a file fallback
with h5py.File(
    os.path.normpath(os.path.join(target_directory, f"{filename}"))
) as fp:
    if nodename in fp.keys():
        final_log.append("this nodename already exists, so I will call it temp")
        nodename = "temp_noPower"
        final_log.append(
            f"I had problems writing to the correct file {filename} so I'm going to try to save this node as temp_noPower"
        )
        vd_data.name(nodename)
# hdf5_write should be outside the h5py.File with block, since it opens the file itself
vd_data.hdf5_write(filename, directory=target_directory)
# }}}
logger.debug("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
logger.debug(strm("Name of saved data", vd_data.name()))
# }}}
input("Now plug the B12 back in and start up the FLInst power control server so we can continue!")
# {{{run enhancement
with power_control() as p:
    # JF points out it should be possible to save time by removing this (b/c we
    # shut off microwave right away), but AG notes that doing so causes an
    # error.  Therefore, debug the root cause of the error and remove it!
    retval_thermal = p.dip_lock(
        config_dict["uw_dip_center_GHz"] - config_dict["uw_dip_width_GHz"] / 2,
        config_dict["uw_dip_center_GHz"] + config_dict["uw_dip_width_GHz"] / 2,
    )
    p.mw_off()
    time.sleep(16.0) #give some time for the power source to "settle"
    p.start_log()
    for j in range(thermal_scans):
        DNP_ini_time = time.time()
        # call B/C to run spin echo
        if j == 0:
            DNP_data = run_spin_echo(
                nScans=config_dict["nScans"],
                indirect_idx=j,
                indirect_len=len(powers) + thermal_scans,
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
            time_axis_coords = DNP_data.getaxis('indirect')
        else:
             DNP_data = run_spin_echo(
                nScans=config_dict["nScans"],
                indirect_idx=j,
                indirect_len=len(powers) + thermal_scans,
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
        # call D to run spin echo
        #Now that the thermal is collected we increment our powers and collect our data at each power
        run_spin_echo(
            nScans=config_dict["nScans"],
            indirect_idx=j + thermal_scans,
            indirect_len=len(powers) + thermal_scans,
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
            ret_data=DNP_data,
        )
        time_axis_coords[j + thermal_scans]["stop_times"] = time.time()
    DNP_data.set_prop("stop_time", time.time())
    DNP_data.set_prop("postproc_type", Ep_postproc)
    DNP_data.set_prop("acq_params", config_dict.asdict())
    DNP_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    if phase_cycling:
        DNP_data.chunk("t", ["ph1", "t2"], [len(Ep_ph1_cyc), -1])
        DNP_data.setaxis("ph1", Ep_ph1_cyc / 4)
        DNP_data.reorder(["ph1", "nScans", "t2"])
    DNP_data.name(config_dict["type"])
    nodename = DNP_data.name()
    try:
        DNP_data.hdf5_write(filename, directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}, so I'm going to try to save your file to temp_ODNP.h5 in the current h5 file"
        )
        target_directory = os.path.getcwd()
        filename = "temp_ctrl.h5"
        if os.path.exists("temp_ODNP.h5"):
            final_log.append("there is a temp_ODNP.h5 already! -- I'm removing it")
            os.remove("temp_ODNP.h5")
            DNP_data.hdf5_write(filename, directory=target_directory)
            final_log.append(
                "if I got this far, that probably worked -- be sure to move/rename temp_ODNP.h5 to the correct name!!")
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
            # call B to run_IR
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
        vd_data.set_prop("start_time", ini_time)
        vd_data.set_prop("stop_time", time.time())
        vd_data.set_prop("acq_params", config_dict.asdict())
        vd_data.set_prop("postproc_type", IR_postproc)
        vd_data.rename("indirect", "vd")
        vd_data.setaxis("vd", vd_list_us * 1e-6).set_units("vd", "s")
        if phase_cycling:
            vd_data.chunk("t", ["ph2", "ph1", "t2"], [len(IR_ph2_cyc), len(IR_ph1_cyc), -1])
            vd_data.setaxis("ph1", IR_ph1_cyc / 4)
            vd_data.setaxis("ph2", IR_ph2_cyc / 4)
        vd_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
        vd_data.name(T1_node_names[j])
        nodename = vd_data.name()
        with h5py.File(
            os.path.normpath(os.path.join(target_directory, filename))
            ) as fp:
            tempcounter = 1
            orig_nodename = nodename
            while nodename in fp.keys():
                nodename = "%s_temp_%d"%(orig_nodename,tempcounter)
                final_log.append("this nodename already exists, so I will call it {nodename}")
                vd_data.name(nodename)
                tempcounter += 1
        # hdf5_write should be outside the h5py.File with block, since it opens the file itself
        vd_data.hdf5_write(filename, directory=target_directory)
        print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
        print(("Name of saved data", vd_data.name()))
    final_frq = p.dip_lock(
        config_dict["uw_dip_center_GHz"] - config_dict["uw_dip_width_GHz"] / 2,
        config_dict["uw_dip_center_GHz"] + config_dict["uw_dip_width_GHz"] / 2,
    )
    this_log = p.stop_log()
# }}}
config_dict.write()
with h5py.File(os.path.join(target_directory, filename), "a") as f:
    log_grp = f.create_group("log")
    hdf_save_dict_to_group(log_grp, this_log.__getstate__())
print('*'*30+'\n'+'\n'.join(final_log))
