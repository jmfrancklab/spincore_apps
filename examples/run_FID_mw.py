"""FID with microwaves
======================
Runs FID at increasing power up to the max power set by the configuration file. Number of steps is also specified in the configuration file. For this script to work the FLInst server must be running to communicate with the B12 for setting powers. The actual output and RX of the microwaves is tracked using the log and start/stop times of each FID acquisition.
"""
from pyspecdata import *
from pyspecdata import strm
from numpy import *
import os, sys, time
import SpinCore_pp
import h5py
from datetime import datetime
from Spincore_pp.ppg import generic
from Instruments import power_control
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
from SpinCore_pp.power_helper import gen_powerlist

target_directory = getDATADIR(exp_type="ODNP_NMR_comp/ODNP")
fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "FID_mw"
config_dict["date"] = date
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
phase_cycling = True
if phase_cycling:
    ph1_cyc = r_[0, 1, 2, 3]
    nPhaseSteps = 4
if not phase_cycling:
    ph1_cyc = 0.0
    nPhaseSteps = 1
# {{{ Parameters for Bridge12
dB_settings = gen_powerlist(
    config_dict["max_power"], config_dict["power_steps"], three_down=False
)
logger.info("dB settings", dB_settings)
logger.info("correspond to powers in Watts", 10 ** (dB_settings / 10.0 - 3))
input("Look ok?")
powers = 1e-3 * 10 ** (dB_settings / 10.0)
# }}}
# {{{ note on timing
# putting all times in microseconds
# as this is generally what the SpinCore takes
# note that acq_time is always milliseconds
# }}}
total_points = len(ph1_cyc) * nPoints
assert total_points < 2**14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"
    % total_points
)
# {{{ run ppg
with power_control() as p:
    retval_thermal = p.dip_lock(
        config_dict["uw_dip_center_GHz"] - config_dict["uw_dip_width_GHz"] / 2,
        config_dict["uw_dip_center_GHz"] + config_dict["uw_dip_width_GHz"] / 2,
    )
    p.mw_off()
    time.sleep(16.0)  # give some time for the power source to "settle"
    p.start_log()
    ini_time = time.time()
    FID = generic(
        ppg=[
            ("marker", "start", 1),
            ("phase_reset", 1),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", config_dict["p90_us"], "ph1", ph1_cyc),
            ("delay", config_dict["deadtime_us"]),
            ("acquire", config_dict["acq_time_ms"]),
            ("delay", config_dict["repetition_us"]),
            ("jumpto", "start"),
        ],
        nScans=config_dict["nScans"],
        indirect_len=len(dB_settings)
        + 1,  # make length long enough to include this no power
        indirect_idx=0,
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        SW_kHz=config_dict["SW_kHz"],
        indirect_fields=("start_times", "stop_times"),
        ret_data=None,
    )
    done_t = time.time()
    time_axis_coords = FID.getaxis("indirect")
    time_axis_coords[0]["start_times"] = ini_time
    time_axis_coords[0]["stop_times"] = done_t
    power_settings_dBm = np.zeros_like(dB_settings)
    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    for j, this_dB in enumerate(dB_settings):
        logger.debug("SETTING THIS POWER", this_dB, "(", dB_settings[j - 1], ")")
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
        time_axis_coords[j + 1]["start_times"] = time.time()
        generic(
            ppg=[
                ("marker", "start", 1),
                ("phase_reset", 1),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", config_dict["p90_us"], "ph1", ph1_cyc),
                ("delay", config_dict["deadtime_us"]),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", config_dict["repetition_us"]),
                ("jumpto", "start"),
            ],
            nScans=config_dict["nScans"],
            indirect_len=len(dB_settings) + 1,
            indirect_idx=j + 1,
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            SW_kHz=config_dict["SW_kHz"],
            indirect_fields=("start_times", "stop_times"),
            ret_data=FID,
        )
        time_axis_coords[j + 1]["stop_times"] = time.time()
    FID.set_prop("acq_params", config_dict.asdict())
    FID.setaxis("nScans", r_[0 : config_dict["nScans"]])
    if phase_cycling:
        FID.chunk("t", ["ph1", "t2"], [len(ph1_cyc), -1])
        FID.setaxis("ph1", ph1_cyc / 4)
        FID.reorder(["ph1", "nScans", "t2"])
    FID.name(config_dict["type"])
    nodename = FID.name()
    try:
        FID.hdf5_write(filename, directory=target_directory)
    except:
        print(
            f"I had problems writing to the correct file {filename}, so I'm going to try to save your file to temp_FID_mw.h5 in the current h5 file"
        )
        target_directory = os.path.getcwd()
        filename = "temp_FID_mw.h5"
        if os.path.exists("temp_FID_mw.h5"):
            final_log.append("there is a temp_FID_mw.h5 already! -- I'm removing it")
            os.remove("temp_FID_mw.h5")
            DNP_data.hdf5_write(filename, directory=target_directory)
            final_log.append(
                "if I got this far, that probably worked -- be sure to move/rename temp_FID_mw.h5 to the correct name!!"
            )
    logger.info("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
    logger.debug(strm("Name of saved data", FID.name()))
    # }}}
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
