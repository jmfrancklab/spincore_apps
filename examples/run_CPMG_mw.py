"""
CPMG with microwaves
====================

Standard CPMG experiment with progressively increasing power. A CPMG is taken at evenly spaced steps up to the maximum power defined in the configuration file
"""
from pylab import *
from pyspecdata import *
from numpy import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import generic
from Instruments import power_control
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
from SpinCore_pp.power_helper import gen_powerlist
from datetime import datetime
import time
import h5py

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "cpmg_mw"
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
# {{{power settings
dB_settings = gen_powerlist(config_dict["max_power"], config_dict["power_steps"],three_down = False)
print("dB_settings", dB_settings)
print("correspond to powers in Watts", 10 ** (dB_settings / 10.0 - 3))
input("Look ok?")
powers = 1e-3 * 10 ** (dB_settings / 10.0)
# }}}
# {{{make better tau
marker = 1.0
tau_extra = 5000.0  # us, must be more than deadtime and more than deblank
pad_start = tau_extra - config_dict["deadtime_us"]
pad_end = tau_extra - config_dict["deblank_us"] * 2  # marker + deblank
twice_tau = (
    config_dict["deblank_us"]
    + 2 * config_dict["p90_us"]
    + config_dict["deadtime_us"]
    + pad_start
    + config_dict["acq_time_ms"] * 1e3
    + pad_end
    + marker
)
tau_us = twice_tau / 2.0
config_dict["tau_us"] = tau_us
# }}}
# {{{run CPMG
with power_control() as p:
    retval_thermal = p.dip_lock(
        config_dict["uw_dip_center_GHz"] - config_dict["uw_dip_width_GHz"] / 2,
        config_dict["uw_dip_center_GHz"] + config_dict["uw_dip_width_GHz"] / 2,
    )
    p.mw_off()
    time.sleep(16.0) #give some time for the power source to "settle"
    p.start_log()
    ini_time = time.time() 
    cpmg_data = generic(
        ppg_list=[
            ("phase_reset", 1),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", config_dict["p90_us"], "ph1", ph1_cyc),
            ("delay", config_dict["tau_us"]),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
            ("delay", config_dict["deadtime_us"]),
            ("delay", pad_start_us),
            ("acquire", config_dict["acq_time_ms"]),
            ("delay", pad_end_us),
            ("marker", "echo_label", (config_dict["nEchoes"] - 1)),  # 1 us delay
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
            ("delay", config_dict["deadtime_us"]),
            ("delay", pad_start_us),
            ("acquire", config_dict["acq_time_ms"]),
            ("delay", pad_end_us),
            ("jumpto", "echo_label"),  # 1 us delay
            ("delay", config_dict["repetition_us"]),
        ],
        nScans=config_dict["nScans"],
        indirect_idx=0,
        indirect_len=len(powers) + 1,
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        SW_kHz=config_dict["SW_kHz"],
        indirect_fields = ("start_times","stop_times")
        ret_data=None,
    )
    done_t = time.time()
    time_axis_coords = cpmg_data.getaxis('indirect')
    time_axis_coords[0]['start_times'] = ini_time
    time_axis_coords[0]['stop_times'] = done_t
    power_settings_dBm = np.zeros_like(dB_settings)
    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    for j, this_dB in enumerate(dB_settings):
        logger.debug(
            "SETTING THIS POWER", this_dB, "(", dB_settings[j - 1], ")"
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
        time_axis_coords[j + 1]["start_times"] = time.time()
        generic(
            ppg_list=[
                ("phase_reset", 1),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", config_dict["p90_us"], "ph1", ph1_cyc),
                ("delay", config_dict["tau_us"]),
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
                ("delay", config_dict["deadtime_us"]),
                ("delay", pad_start_us),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", pad_end_us),
                ("marker", "echo_label", (config_dict["nEchoes"] - 1)),  # 1 us delay
                ("delay_TTL", config_dict["deblank_us"]),
                ("pulse_TTL", 2.0 * config_dict["p90_us"], 0.0),
                ("delay", config_dict["deadtime_us"]),
                ("delay", pad_start_us),
                ("acquire", config_dict["acq_time_ms"]),
                ("delay", pad_end_us),
                ("jumpto", "echo_label"),  # 1 us delay
                ("delay", config_dict["repetition_us"]),
            ],
            nScans=config_dict["nScans"],
            indirect_idx=j+1,
            indirect_len=len(powers) + 1,
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=config_dict["carrierFreq_MHz"],
            nPoints=nPoints,
            SW_kHz=config_dict["SW_kHz"],
            indirect_fields = ("start_times","stop_times")
            ret_data=cpmg_data,
        )
        time_axis_coords[j+1]['stop_times'] = time.time()
    cpmg_data.setaxis('nScans',r_[0:config_dict['nScans']])
    cpmg_data.name(config_dict["type"] + "_" + config_dict["cpmg_counter"])
    cpmg_data.set_prop("acq_params", config_dict.asdict())
    target_directory = getDATADIR(exp_type="ODNP_NMR_comp/CPMG")
    filename_out = filename + ".h5"
    nodename = cpmg_data.name()
    if os.path.exists(f"{filename_out}"):
        print("this file already exists so we will add a node to it!")
        with h5py.File(
            os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
        ) as fp:
            if nodename in fp.keys():
                print("this nodename already exists, so I will call it temp_cpmg_mw")
                cpmg_data.name("temp_cpmg_mw")
                nodename = "temp_cpmg_mw"
        cpmg_data.hdf5_write(f"{filename_out}", directory=target_directory)
    else:
        try:
            cpmg_data.hdf5_write(f"{filename_out}", directory=target_directory)
        except:
            print(
                f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_cpmg_mw.h5 in the current directory"
            )
            if os.path.exists("temp_cpmg_mw.h5"):
                print("there is a temp_cpmg_mw.h5 already! -- I'm removing it")
                os.remove("temp.h5")
                cpmg_data.hdf5_write("temp_spmg_mw.h5")
                print(
                    "if I got this far, that probably worked -- be sure to move/rename temp_cpmg_mw.h5 to the correct name!!"
                )
    print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
    print(("Name of saved data", echo_data.name()))
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
fl.show()
