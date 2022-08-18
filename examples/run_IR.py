"""Run Inversion Recovery at set power
======================================
You will need to manually set the power manually with Spyder and the B12. Once the power is set and the parameters are adjusted, you can run this program to collect the inversion recovery dataset at the set power.
"""
from pyspecdata import *
import os
import h5py
from SpinCore_pp.power_helper import gen_powerlist
from Instruments import power_control
import SpinCore_pp
from SpinCore_pp.ppg import run_IR
from datetime import datetime
import time
fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# NOTE: Number of segments is nEchoes * nPhaseSteps
# {{{create filename and save to config file
IR_input = input("Is this going to be added to a ODNP set?")
date = datetime.now().strftime("%y%m%d")
config_dict["date"] = date
if IR_input.lower().startswith("n"):
    config_dict["type"] = "IR"
    config_dict["IR_counter"] += 1
    filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
    target_directory = getDATADIR(exp_type="ODNP_NMR_comp/inv_rec")
elif IR_input.lower().startwith("y"):
    config_dict['type'] = 'ODNP'
    filename = f"{config_dict['data']}_{config_dict['chemical']}_{config_dict['type']}_{config_dict['odnp_counter']}"
    config_dict['type'] = 'IR'
    config_dict["IR_counter"] += 1
    target_directory = getDATADIR(exp_type="ODNP_NMR_comp/ODNP")
filename_out = filename + ".h5"
# }}}
# {{{phase cycling
phase_cycling = True
if phase_cycling:
    ph1 = r_[0, 2]
    ph2 = r_[0, 2]
    nPhaseSteps = 4
if not phase_cycling:
    ph1 = r_[0]
    ph2 = r_[0]
    nPhaseSteps = 1
total_pts = nPoints * nPhaseSteps
assert total_pts < 2 ** 14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"
    % total_pts
)
# }}}
# {{{make vd list
vd_kwargs = {
    j: config_dict[j]
    for j in ["krho_cold", "krho_hot", "T1water_cold", "T1water_hot"]
    if j in config_dict.keys()
}
vd_list_us = (
    SpinCore_pp.vdlist_from_relaxivities(config_dict["concentration"], **vd_kwargs)
    * 1e6
)  # put vd list into microseconds
# }}}
#{{{ power settings
T1_powers_dB = gen_powerlist(config_dict['max_power'], config_dict['num_T1s'], three_down=False)
T1_node_names = ["FIR_%ddBm" % j for j in T1_powers_dB]
logger.info("T1_powers_dB", T1_powers_dB)
logger.info("correspond to powers in Watts", 10 ** (T1_powers_dB / 10.0 - 3))
myinput = input("Look ok?")
if myinput.lower().startswith("n"):
    raise ValueError("you said no!!!")
#}}}
#{{{run IR
vd_data = run_IR(
    nPoints=nPoints,
    nEchoes=config_dict['nEchoes'],
    vd_list_us=vd_list_us,
    nScans=config_dict['thermal_nScans'],
    adcOffset=config_dict['adc_offset'],
    carrierFreq_MHz=config_dict['carrierFreq_MHz'],
    p90_us=config_dict['p90_us'],
    tau_us=config_dict['tau_us'],
    repetition=config_dict['FIR_rep'],
    output_name=filename,
    SW_kHz=config_dict['SW_kHz'],
    ret_data=None,
)
vd_data.set_prop("acq_params", config_dict.asdict())
vd_data.set_prop("postproc_type", "spincore_IR_v1")
vd_data.name("FIR_noPower")
vd_data.chunk("t", ["ph2", "ph1", "t2"], [len(ph1), len(ph2), -1])
vd_data.setaxis("ph1", ph1 / 4)
vd_data.setaxis("ph2", ph2 / 4)
vd_data.setaxis('nScans',r_[0:config_dict['thermal_nScans']])
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
with power_control() as p:
    for j, this_dB in enumerate(T1_powers_dB):
        if j == 0:
            MWfreq = p.dip_lock(
                config_dict['uw_dip_center_GHz'] - config_dict['uw_dip_width_GHz'] / 2,
                config_dict['uw_dip_center_GHz'] + config_dict['uw_dip_width_GHz'] / 2,
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
        vd_data = run_IR(
            nPoints=nPoints,
            nEchoes=config_dict['nEchoes'],
            vd_list_us=vd_list_us,
            nScans=config_dict['nScans'],
            adcOffset=config_dict['adc_offset'],
            carrierFreq_MHz=config_dict['carrierFreq_MHz'],
            p90_us=config_dict['p90_us'],
            tau_us=config_dict['tau_us'],
            repetition=config_dict['FIR_rep'],
            output_name= filename,
            SW_kHz=config_dict['SW_kHz'],
            ret_data=None,
        )
        vd_data.set_prop("acq_params", config_dict.asdict())
        vd_data.set_prop("postproc_type", "spincore_IR_v1")
        vd_data.name(T1_node_names[j])
        vd_data.chunk("t", ["ph2", "ph1", "t2"], [len(ph2), len(ph1), -1])
        vd_data.setaxis("ph1", ph1 / 4)
        vd_data.setaxis("ph2", ph2 / 4)
        vd_data.setaxis('nScans',r_[0:config_dict['nScans']])
        nodename = vd_data.name()
        with h5py.File(
            os.path.normpath(os.path.join(target_directory,f"{filename_out}")
        )) as fp:
            if nodename in fp.keys():
                print("this nodename already exists, so I will call it temp_%d"%j)
                vd_data.name("temp_%d"%j)
                nodename = "temp_%d"%j
                vd_data.hdf5_write(f"{filename_out}",directory = target_directory)
            else:
                try:
                    vd_data.hdf5_write(f"{filename_out}", directory=target_directory)
                except:
                    print(
                        f"I had problems writing to the correct file {filename}.h5, so I'm going to try to save your file to temp_IR_%d.h5 in the current directory"%config_dict['ir_counter'])
                    )
                    if os.path.exists("temp_IR_%d.h5"%config_dict['ir_counter']):
                        print("there is a temp_IR_%d.h5 already! -- I'm removing it"%config_dict['ir_counter'])
                        os.remove("temp_IR_%d.h5"%config_dict['ir_counter'])
                        vd_data.hdf5_write("temp_IR_%d.h5"%config_dict['ir_counter'])
                        print(
                            "if I got this far, that probably worked -- be sure to move/rename temp_IR_%d.h5 to the correct name!!"%config_dict['ir_counter']
                        )
        print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
        print(("Name of saved data", vd_data.name()))
        print(("Shape of saved data", ndshape(vd_data)))
    final_frq = p.dip_lock(
        config_dict['uw_dip_center_GHz'] - config_dict['uw_dip_width_GHz'] / 2,
        config_dict['uw_dip_center_GHz'] + config_dict['uw_dip_width_GHz'] / 2,
    )
# }}}
config_dict.write()
# }}}
# {{{visualize raw data
vd_data.ift("t2")
fl.next("raw data for highest power")
fl.image(vd_data.setaxis("vd", "#"))
fl.next("abs raw data for highest power")
fl.image(abs(vd_data).setaxis("vd", "#"))
vd_data.ft("t2")
fl.next("FT raw data for highest power")
fl.image(vd_data.setaxis("vd", "#"))
fl.next("FT abs raw data for highest power")
fl.image(abs(vd_data).setaxis("vd", "#")["t2":(-1e3, 1e3)])
fl.show()
# }}}
