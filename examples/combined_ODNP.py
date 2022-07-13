'''Automated Combined DNP with Log
==================================
This needs to be run in sync with the power control server. To do so:
    1. Open Xepr on EPR computer, connect to spectrometer, enable XEPR_API and then in new terminal, run XEPR_API_server.py. When this is ready to go you will see it say "I am listening".
    2. Open new terminal on NMR computer, move into git/inst_notebooks/Instruments and run wipty power_control_server.py. When this is ready to go it will read "I am listening"
Once the power control server is up and ready to go you may run this script to collect the enhancement data as well as a series of IRs at increasing power collected in sync with a time log.
'''
import numpy as np
import pyspecdata as psp
import os, sys, time
import SpinCore_pp
from numpy import r_
from Instruments import power_control
from datetime import datetime
from SpinCore_pp.ppg import run_spin_echo, run_IR
# do the same with the inversion recovery
from SpinCore_pp.power_helper import gen_powerlist
from pyspecdata.file_saving.hdf_save_dict_to_group import hdf_save_dict_to_group
import h5py
from config_parser_fn import parser_function
logger = psp.init_logging(level="debug")
fl = psp.figlist_var()
# {{{ import acquisition parameters
values, config = parser_function('active.ini')
nPoints = int(values['acq_time_ms']*values['SW_kHz']+0.5)
#}}}
#{{{create filename and save to config file
date = datetime.now().strftime('%y%m%d')
config.set('file_names','type','enhancement')
config.set('file_names','date',f'{date}')
odnp_number = values['odnp_number'])
odnp_number += 1
config.set('file_names','odnp_number',str(odnp_number))
config.write(open('active.ini','w')) #write edits to config file
values, config = parser_function('active.ini') #translate changes in config file to our dict
filename = values['date']+'_'+values['chemical']+'_'+values['type']+'_'+values['odnp_counter']
#}}}
vd_list_us = np.linspace(5e1,0.5e6,5)
# {{{Power settings
dB_settings = gen_powerlist(values['max_power'], values['power_steps'] + 1, three_down=True)
T1_powers_dB = gen_powerlist(values['max_power'], values['num_T1s'], three_down=False)
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
myfilename = filename + ".h5"
if os.path.exists(myfilename):
    raise ValueError(
        "the file %s already exists, so I'm not going to let you proceed!" % myfilename
    )
# }}}
# {{{run enhancement
DNP_ini_time = time.time()
with power_control() as p:
    # JF points out it should be possible to save time by removing this (b/c we
    # shut off microwave right away), but AG notes that doing so causes an
    # error.  Therefore, debug the root cause of the error and remove it!
    retval_thermal = p.dip_lock(
        values['uw_dip_center_GHz'] - values['uw_dip_width_GHz'] / 2,
        values['uw_dip_center_GHz'] + values['uw_dip_width_GHz'] / 2,
    )
    p.start_log()
    p.mw_off()
    DNP_data = run_spin_echo(
        nScans=values['nScans'],
        indirect_idx=0,
        indirect_len=len(powers) + 1,
        ph1_cyc=Ep_ph1_cyc,
        adcOffset=values['adc_offset'],
        carrierFreq_MHz=values['carrierFreq_MHz'],
        nPoints=nPoints,
        nEchoes=values['nEchoes'],
        p90_us=values['p90_us'],
        repetition=values['repetition_us'],
        tau_us=values['tau_us'],
        SW_kHz=values['SW_kHz'],
        output_name=filename,
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
    DNP_data.set_prop("Ep_start_time", DNP_ini_time)
    DNP_data.set_prop("Ep_thermal_done_time", DNP_thermal_done)
    time_axis_coords[0]["stop_times"] = DNP_thermal_done
    power_settings_dBm = np.zeros_like(dB_settings)
    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    for j, this_dB in enumerate(dB_settings):
        logger.debug(
            "SETTING THIS POWER", this_dB, "(", dB_settings[j - 1], powers[j], "W)"
        )
        if j == 0:
            retval = p.dip_lock(
                values['uw_dip_center_GHz'] - values['uw_dip_width_GHz'] / 2,
                values['uw_dip_center_GHz'] + values['uw_dip_width_GHz'] / 2,
            )
        logger.debug("done with dip lock 1")
        p.set_power(this_dB)
        logger.debug("power was set")
        for k in range(10):
            time.sleep(0.5)
            if p.get_power_setting() >= this_dB:
                break
        if p.get_power_setting() < this_dB:
            raise ValueError("After 10 tries, the power has still not settled")
        time.sleep(5)
        power_settings_dBm[j] = p.get_power_setting()
        time_axis_coords[j + 1]["start_times"] = time.time()
        logger.debug("gonna run the Ep for this power")
        run_spin_echo(
            nScans=values['nScans'],
            indirect_idx=j + 1,
            indirect_len=len(powers) + 1,
            adcOffset=values['adc_offset'],
            carrierFreq_MHz=values['carrierFreq_MHz'],
            nPoints=nPoints,
            nEchoes=values['nEchoes'],
            p90_us=values['p90_us'],
            repetition=values['repetition_us'],
            tau_us=values['tau_us'],
            SW_kHz=values['SW_kHz'],
            output_name=filename,
            ret_data=DNP_data,
        )
        time_axis_coords[j + 1]["stop_times"] = time.time()
DNP_data.set_prop("stop_time", time.time())
DNP_data.set_prop("postproc_type", "spincore_ODNP_v3")
DNP_data.set_prop("acq_params", values)
DNP_data.name(values['type'])
DNP_data.chunk("t", ["ph1", "t2"], [4, -1])
DNP_data.setaxis("ph1", Ep_ph1_cyc / 4)
logger.info("SAVING FILE... %s" % myfilename)
DNP_data.hdf5_write(myfilename)
logger.info("FILE SAVED")
logger.debug("Name of saved enhancement data", DNP_data.name())
logger.debug("shape of saved enhancement data", psp.ndshape(DNP_data))
# }}}
# {{{run IR
with power_control() as p:
    retval_IR = p.dip_lock(
        values['uw_dip_center_GHz'] - values['uw_dip_width_GHz'] / 2,
        values['uw_dip_center_GHz'] + values['uw_dip_width_GHz'] / 2,
    )
    p.mw_off()
    ini_time = time.time()  # needed b/c data object doesn't exist yet
    vd_data = run_IR(
        nPoints=nPoints,
        nEchoes=values['nEchoes'],
        vd_list_us=vd_list_us,
        nScans=values['nScans'],
        adcOffset=values['adc_offset'],
        carrierFreq_MHz=values['carrierFreq_MHz'],
        p90_us=values['p90_us'],
        tau_us=values['tau_us'],
        repetition=values['FIR_rep'],
        output_name=filename,
        SW_kHz=values['SW_kHz'],
        ph1_cyc=IR_ph1_cyc,
        ph2_cyc=IR_ph2_cyc,
        ret_data=None,
    )
    vd_data.set_prop("start_time", ini_time)
    vd_data.set_prop("stop_time", time.time())
    meter_power = -999
    vd_data.set_prop("acq_params", values)
    vd_data.set_prop("postproc_type", "spincore_IR_v1")
    vd_data.name("FIR_noPower")
    vd_data.chunk("t", ["ph1", "ph2", "t2"], [len(IR_ph1_cyc), len(IR_ph2_cyc), -1])
    vd_data.setaxis("ph1", IR_ph1_cyc / 4)
    vd_data.setaxis("ph2", IR_ph2_cyc / 4)
    # Need error handling (JF has posted something on this..)
    vd_data.hdf5_write(myfilename)
    logger.debug("\n*** FILE SAVED ***\n")
    logger.debug("Name of saved data", vd_data.name())
    for j, this_dB in enumerate(T1_powers_dB):
        if j == 0:
            MWfreq = p.dip_lock(
                values['uw_dip_center_GHz'] - values['uw_dip_width_GHz'] / 2,
                values['uw_dip_center_GHz'] + values['uw_dip_width_GHz'] / 2,
            )
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
        vd_data = run_IR(
            nPoints=nPoints,
            nEchoes=values['nEchoes'],
            vd_list_us=vd_list_us,
            nScans=values['nScans'],
            adcOffset=values['adc_offset'],
            carrierFreq_MHz=values['carrierFreq_MHz'],
            p90_us=values['p90_us'],
            tau_us=values['tau_us'],
            repetition=values['FIR_rep'],
            output_name= filename,
            SW_kHz=values['SW_kHz'],
            ret_data=None,
        )
        vd_data.set_prop("start_time", ini_time)
        vd_data.set_prop("stop_time", time.time())
        vd_data.set_prop("acq_params", values)
        vd_data.set_prop("postproc_type", "spincore_IR_v1")
        vd_data.name(T1_node_names[j])
        vd_data.chunk("t", ["ph1", "ph2", "t2"], [len(IR_ph1_cyc), len(IR_ph2_cyc), -1])
        vd_data.setaxis("ph1", IR_ph1_cyc / 4)
        vd_data.setaxis("ph2", IR_ph2_cyc / 4)
        vd_data.hdf5_write(myfilename)
    final_frq = p.dip_lock(
        values['uw_dip_center_GHz'] - values['uw_dip_width_GHz'] / 2,
        values['uw_dip_center_GHz'] + values['uw_dip_width_GHz'] / 2,
    )
    this_log = p.stop_log()
SpinCore_pp.stopBoard()
# }}}
with h5py.File(myfilename, "a") as f:
    log_grp = f.create_group("log")
    hdf_save_dict_to_group(log_grp, this_log.__getstate__())
