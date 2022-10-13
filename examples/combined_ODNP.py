'''Automated Combined DNP with Log
==================================
This needs to be run in sync with the power control server. To do so:
    1. Open Xepr on EPR computer, connect to spectrometer, enable XEPR_API and then in new terminal, run XEPR_API_server.py. When this is ready to go you will see it say "I am listening".
    2. Open new terminal on NMR computer, move into git/inst_notebooks/Instruments and run wipty power_control_server.py. When this is ready to go it will read "I am listening"
Once the power control server is up and ready to go you may run this script to collect the enhancement data as well as a series of IRs at increasing power collected in sync with a time log.
'''
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
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/ODNP")
fl = figlist_var()
# {{{ import acquisition parameters
parser_dict = SpinCore_pp.configuration('active.ini')
nPoints = int(parser_dict['acq_time_ms']*parser_dict['SW_kHz']+0.5)
#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
parser_dict['type'] = 'ODNP'
parser_dict['date'] = date
parser_dict['odnp_counter'] += 1
filename = f"{parser_dict['date']}_{parser_dict['chemical']}_{parser_dict['type']}_{parser_dict['odnp_counter']}"
filename_out = filename + ".h5"
#}}}
#{{{Make VD list based on concentration
vd_kwargs = {
        j:parser_dict[j]
        for j in ['krho_cold','krho_hot','T1water_cold','T1water_hot']
        if j in parser_dict.keys()
        }
vd_list_us = SpinCore_pp.vdlist_from_relaxivities(parser_dict['concentration'],**vd_kwargs) * 1e6 #convert to microseconds
#}}}
# {{{Power settings
dB_settings = gen_powerlist(parser_dict['max_power'], parser_dict['power_steps'] + 1, three_down=True)
T1_powers_dB = gen_powerlist(parser_dict['max_power'], parser_dict['num_T1s'], three_down=False)
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
#{{{phase cycling
Ep_ph1_cyc = r_[0, 1, 2, 3]
total_points = len(Ep_ph1_cyc)*nPoints
assert total_points < 2**14, "For Ep: You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
IR_ph1_cyc = r_[0, 2]
IR_ph2_cyc = r_[0, 2]
total_pts = len(IR_ph2_cyc)*len(IR_ph1_cyc)*nPoints
assert total_pts < 2**14, "For IR: You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"%total_pts
#}}}
# {{{ check for file
if os.path.exists(filename_out):
    raise ValueError(
        "the file %s already exists, so I'm not going to let you proceed!" % filename_out
    )
input("B12 needs to be unplugged and turned off for the thermal! Don't have the power server running just yet")
# }}}
# {{{Collect Thermals - serves as a control to compare the thermal of Ep to ensure no microwaves were leaking
control_thermal = run_spin_echo(
    nScans=parser_dict['thermal_nScans'],
    indirect_idx=0,
    indirect_len=len(powers) + 1,
    ph1_cyc=Ep_ph1_cyc,
    adcOffset=parser_dict['adc_offset'],
    carrierFreq_MHz=parser_dict['carrierFreq_MHz'],
    nPoints=nPoints,
    nEchoes=parser_dict['nEchoes'],
    p90_us=parser_dict['p90_us'],
    repetition=parser_dict['repetition_us'],
    tau_us=parser_dict['tau_us'],
    SW_kHz=parser_dict['SW_kHz'],
    indirect_fields=("start_times", "stop_times"),
    ret_data=None,
)  # assume that the power axis is 1 longer than the
#                         "powers" array, so that we can also store the
#                         thermally polarized signal in this array (note
#                         that powers and other parameters are defined
#                         globally w/in the script, as this function is not
#                         designed to be moved outside the module
control_thermal = control_thermal['nScans',-1:]
control_thermal.set_prop("postproc_type", "spincore_ODNP_v3")
control_thermal.set_prop("acq_params", parser_dict.asdict())
control_thermal.chunk("t", ["ph1", "t2"], [len(Ep_ph1_cyc), -1])
control_thermal.setaxis("ph1", Ep_ph1_cyc / 4)
control_thermal.setaxis('nScans',r_[0:parser_dict['nScans']])
control_thermal.reorder(['ph1','nScans','t2'])
control_thermal.ft('t2',shift=True)
control_thermal.ft(['ph1'], unitary = True)
control_thermal.name('control_thermal')
nodename = control_thermal.name()
try:
    control_thermal.hdf5_write(f"{filename_out}",directory = target_directory)
except:
    print(f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_ctrl.h5 in the current directory"
        )
    if os.path.exists("temp_ctrl.h5"):
        print("There is already a temp_ctrl.h5 -- I'm removing it")
        os.remove("temp_ctrl.h5")
        DNP_data.hdf5_write("temp_ctrl.h5", directory=target_directory)
        filename_out = "temp_ctrl.h5"
        input("change the name accordingly once this is done running!")
logger.info("FILE SAVED")
logger.debug(strm("Name of saved controlled thermal", control_thermal.name()))
logger.debug("shape of saved controlled thermal", ndshape(control_thermal))
# }}}
#{{{IR at no power
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
        nScans=config_dict["nScans"],
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        p90_us=config_dict["p90_us"],
        tau_us=config_dict["tau_us"],
        repetition=config_dict["repetition_us"],
        ph1_cyc=ph1,
        ph2_cyc=ph2,
        SW_kHz=config_dict["SW_kHz"],
        ret_data=vd_data,
    )
vd_data.rename("indirect","vd")
vd_data.setaxis("vd", vd_list_us * 1e-6).set_units("vd", "s")
vd_data.set_prop('stop_time',time.time())
vd_data.set_prop('start_time',ini_time)
vd_data.set_prop("acq_params", parser_dict.asdict())
vd_data.set_prop("postproc_type", "spincore_IR_v1")
vd_data.name("FIR_noPower")
vd_data.chunk("t", ["ph2", "ph1", "t2"], [len(IR_ph1_cyc), len(IR_ph2_cyc), -1])
vd_data.setaxis("ph1", IR_ph1_cyc / 4)
vd_data.setaxis("ph2", IR_ph2_cyc / 4)
vd_data.setaxis('nScans',r_[0:parser_dict['thermal_nScans']])
nodename = vd_data.name()
with h5py.File(
    os.path.normpath(os.path.join(target_directory, f"{filename_out}")
)) as fp:
    if nodename in fp.keys():
        print("this nodename already exists, so I will call it temp")
        vd_data.name("temp_noPower")
        nodename = "temp_noPower"
        vd_data.hdf5_write(f"{filename_out}",directory=target_directory)
        input(f"I had problems writing to the correct file {filename_out} so I'm going to try to save this node as temp_noPower")
    else:
        vd_data.hdf5_write(f"{filename_out}",directory = target_directory)    
logger.debug("\n*** FILE SAVED ***\n")
logger.debug(strm("Name of saved data", vd_data.name()))
#}}}
# {{{run enhancement
input("Now plug the B12 back in and start up the power_server so we can continue!")
with power_control() as p:
    # JF points out it should be possible to save time by removing this (b/c we
    # shut off microwave right away), but AG notes that doing so causes an
    # error.  Therefore, debug the root cause of the error and remove it!
    retval_thermal = p.dip_lock(
        parser_dict['uw_dip_center_GHz'] - parser_dict['uw_dip_width_GHz'] / 2,
        parser_dict['uw_dip_center_GHz'] + parser_dict['uw_dip_width_GHz'] / 2,
    )
    p.mw_off()
    time.sleep(16.0)
    p.start_log()
    DNP_ini_time = time.time()
    DNP_data = run_spin_echo(
        nScans=parser_dict['nScans'],
        indirect_idx=0,
        indirect_len=len(powers) + 1,
        ph1_cyc=Ep_ph1_cyc,
        adcOffset=parser_dict['adc_offset'],
        carrierFreq_MHz=parser_dict['carrierFreq_MHz'],
        nPoints=nPoints,
        nEchoes=parser_dict['nEchoes'],
        p90_us=parser_dict['p90_us'],
        repetition=parser_dict['repetition_us'],
        tau_us=parser_dict['tau_us'],
        SW_kHz=parser_dict['SW_kHz'],
        indirect_fields=("start_times", "stop_times"),
        ret_data=None,
    )  # assume that the power axis is 1 longer than the
    #                         "powers" array, so that we can also store the
    #                         thermally polarized signal in this array (note
    #                         that powers and other parameters are defined
    #                         globally w/in the script, as this function is not
    #                         designed to be moved outside the module
    DNP_thermal_done = time.time()
    time_axis_coords = DNP_data.getaxis("indirect")
    time_axis_coords[0]["start_times"] = DNP_ini_time
    time_axis_coords[0]["stop_times"] = DNP_thermal_done
    power_settings_dBm = np.zeros_like(dB_settings)
    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    for j, this_dB in enumerate(dB_settings):
        logger.debug(
            "SETTING THIS POWER", this_dB, "(", dB_settings[j - 1], powers[j], "W)"
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
        run_spin_echo(
            nScans=parser_dict['nScans'],
            indirect_idx=j + 1,
            indirect_len=len(powers) + 1,
            adcOffset=parser_dict['adc_offset'],
            carrierFreq_MHz=parser_dict['carrierFreq_MHz'],
            nPoints=nPoints,
            nEchoes=parser_dict['nEchoes'],
            p90_us=parser_dict['p90_us'],
            repetition=parser_dict['repetition_us'],
            tau_us=parser_dict['tau_us'],
            SW_kHz=parser_dict['SW_kHz'],
            ret_data=DNP_data,
        )
        time_axis_coords[j + 1]["stop_times"] = time.time()
    DNP_data.set_prop("stop_time", time.time())
    DNP_data.set_prop("postproc_type", "spincore_ODNP_v4")
    DNP_data.set_prop("acq_params", parser_dict.asdict())
    DNP_data.chunk("t", ["ph1", "t2"], [len(Ep_ph1_cyc), -1])
    DNP_data.setaxis("ph1", Ep_ph1_cyc / 4)
    DNP_data.setaxis('nScans',r_[0:parser_dict['nScans']])
    DNP_data.reorder(['ph1','nScans','t2'])
    DNP_data.name(parser_dict['type'])
    nodename = DNP_data.name()
    try:
        DNP_data.hdf5_write(f"{filename_out}",directory = target_directory)
    except:
        print(f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp.h5 in the current directory"
            )
        if os.path.exists("temp.h5"):
            print("There is already a temp.h5 -- I'm removing it")
            os.remove("temp.h5")
            DNP_data.hdf5_write("temp.h5", directory=target_directory)
            filename_out = "temp.h5"
            input("change the name accordingly once this is done running!")
    logger.info("FILE SAVED")
    logger.debug(strm("Name of saved enhancement data", DNP_data.name()))
    logger.debug("shape of saved enhancement data", ndshape(DNP_data))
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
                vd=vd,
                nScans=config_dict["nScans"],
                adcOffset=config_dict["adc_offset"],
                carrierFreq_MHz=config_dict["carrierFreq_MHz"],
                p90_us=config_dict["p90_us"],
                tau_us=config_dict["tau_us"],
                repetition=config_dict["repetition_us"],
                ph1_cyc=ph1,
                ph2_cyc=ph2,
                SW_kHz=config_dict["SW_kHz"],
                ret_data=vd_data,
            )
        vd_data.rename("indirect","vd")
        vd_data.setaxis("vd", vd_list_us * 1e-6).set_units("vd", "s")
        vd_data.set_prop("start_time", ini_time)
        vd_data.set_prop("stop_time", time.time())
        vd_data.set_prop("acq_params", parser_dict.asdict())
        vd_data.set_prop("postproc_type", "spincore_IR_v1")
        vd_data.name(T1_node_names[j])
        vd_data.chunk("t", ["ph2", "ph1", "t2"], [len(IR_ph2_cyc), len(IR_ph1_cyc), -1])
        vd_data.setaxis("ph1", IR_ph1_cyc / 4)
        vd_data.setaxis("ph2", IR_ph2_cyc / 4)
        vd_data.setaxis('nScans',r_[0:parser_dict['nScans']])
        nodename = vd_data.name()
        with h5py.File(
            os.path.normpath(os.path.join(target_directory,f"{filename_out}")
        )) as fp:
            if nodename in fp.keys():
                print("this nodename already exists, so I will call it temp_%d"%j)
                vd_data.name("temp_%d"%this_dB)
                nodename = "temp_%d"%this_dB
                vd_data.hdf5_write(f"{filename_out}",directory = target_directory)
            else:
                vd_data.hdf5_write(f"{filename_out}", directory=target_directory)
        print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
        print(("Name of saved data", vd_data.name()))
        print(("Shape of saved data", ndshape(vd_data)))
        final_frq = p.dip_lock(
            parser_dict['uw_dip_center_GHz'] - parser_dict['uw_dip_width_GHz'] / 2,
            parser_dict['uw_dip_center_GHz'] + parser_dict['uw_dip_width_GHz'] / 2,
        )
    this_log = p.stop_log()
# }}}
parser_dict.write()
with h5py.File(os.path.join(target_directory, f'{filename_out}'), "a") as f:
    log_grp = f.create_group("log")
    hdf_save_dict_to_group(log_grp, this_log.__getstate__())
