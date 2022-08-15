""" Field Sweep at constant power
=================================
Here we will perform a series of echoes at a range of designated field values. This is normally run at a power of 3-4 W. To run this experiment, please open Xepr on the EPR computer, connect to spectrometer, enable XEPR_API. Then, in a separate terminal, run the program XEPR_API_server.py, wait for it to tell you 'I am listening' - then, you should be able to run this program in sync with the power_control_server.
To run this in sync with the power_control_server, open a separate terminal on the NMR computer and move into git/inst_notebooks/Instruments and run winpty power_control_server(). This will print out "I am listening" when it is ready to go. You can then proceed to run this script to collect your field sweep data
"""
from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
import numpy as np
from Instruments import power_control, Bridge12, prologix_connection, gigatronics
from Instruments.XEPR_eth import xepr
import h5py

fl = figlist_var()
mw_freqs = []
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
# }}}
#{{{make field axis
left = (((config_dict['guessed_mhz_to_ghz']*config_dict['mw_freqs'])/config_dict['gamma_eff_MHz_G']))/1e9
left = left - (config_dict['field_width']/2)
right = (((config_dict['guessed_mhz_to_ghz']*config_dict['mw_freqs'])/config_dict['gamma_eff_MHz_G']))/1e9
right = right + (config_dict['field_width']/2)
field_axis = r_[left:right:1.0]
#}}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "field"
config_dict["date"] = date
config_dict["field_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
# }}}
# {{{phase cycling
print("Here is my field axis:", field_axis)
phase_cycling = True
if phase_cycling:
    nPhaseSteps = 4
if not phase_cycling:
    nPhaseSteps = 1
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{ Parameters for Bridge12
powers = r_[config_dict["max_power"]]
min_dBm_step = 0.5
for x in range(len(powers)):
    dB_settings = (
        round(10 * (log10(powers[x]) + 3.0) / min_dBm_step) * min_dBm_step
    )  # round to nearest min_dBm_step
print("dB_settings", dB_settings)
print("correspond to powers in Watts", 10 ** (dB_settings / 10.0 - 3))
input("Look ok?")
powers = 1e-3 * 10 ** (dB_settings / 10.0)
# }}}
# {{{run field sweep
total_pts = nPoints * nPhaseSteps
assert total_pts < 2 ** 14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"
    % total_pts
)
with power_control() as p:
    dip_f = p.dip_lock(
        config_dict["uw_dip_center_GHz"] - config_dict["uw_dip_width_GHz"] / 2,
        config_dict["uw_dip_center_GHz"] + config_dict["uw_dip_width_GHz"] / 2,
    )
    config_dict["mw_freqs"] = "%.9f" % dip_f
    p.set_power(dB_settings)
    for k in range(10):
        time.sleep(0.5)
        if p.get_power_setting() >= dB_settings:
            break
    if p.get_power_setting() < dB_settings:
        raise ValueError("After 10 tries, this power has still not settled")
    meter_powers = np.zeros_like(dB_settings)
    with xepr() as x_server:
        first_B0 = x_server.set_field(field_axis[0])
        time.sleep(3.0)
        carrierFreq_MHz = config_dict["gamma_eff_MHz_G"] * first_B0
        sweep_data = run_spin_echo(
            nScans=config_dict["nScans"],
            indirect_idx=0,
            indirect_len=len(field_axis),
            adcOffset=config_dict["adc_offset"],
            carrierFreq_MHz=carrierFreq_MHz,
            nPoints=nPoints,
            nEchoes=config_dict["nEchoes"],
            p90_us=config_dict["p90_us"],
            repetition=config_dict["repetition_us"],
            tau_us=config_dict["tau_us"],
            SW_kHz=config_dict["SW_kHz"],
            output_name=filename,
            indirect_fields=("Field", "carrierFreq"),
            ret_data=None,
        )
        myfreqs_fields = sweep_data.getaxis("indirect")
        myfreqs_fields[0]["Field"] = first_B0
        myfreqs_fields[0]["carrierFreq"] = config_dict["carrierFreq_MHz"]
        for B0_index, desired_B0 in enumerate(field_axis[1:]):
            true_B0 = x_server.set_field(desired_B0)
            logging.info("My field in G is %f" % true_B0)
            time.sleep(3.0)
            new_carrierFreq_MHz = config_dict["gamma_eff_MHz_G"] * true_B0
            myfreqs_fields[B0_index + 1]["Field"] = true_B0
            myfreqs_fields[B0_index + 1]["carrierFreq"] = new_carrierFreq_MHz
            logging.info("My frequency in MHz is", new_carrierFreq_MHz)
            run_spin_echo(
                nScans=config_dict["nScans"],
                indirect_idx=B0_index + 1,
                indirect_len=len(field_axis),
                adcOffset=config_dict["adc_offset"],
                carrierFreq_MHz=new_carrierFreq_MHz,
                nPoints=nPoints,
                nEchoes=config_dict["nEchoes"],
                p90_us=config_dict["p90_us"],
                repetition=config_dict["repetition_us"],
                tau_us=config_dict["tau_us"],
                SW_kHz=config_dict["SW_kHz"],
                output_name=filename,
                ret_data=sweep_data,
            )
        SpinCore_pp.stopBoard();
sweep_data.set_prop('acq_params',config_dict.asdict())
# }}}
# {{{chunk and save data
if phase_cycling:
    sweep_data.chunk("t", ["ph1", "t2"], [4, -1])
    sweep_data.setaxis("ph1", r_[0.0, 1.0, 2.0, 3.0] / 4)
    if config_dict["nScans"] > 1:
        sweep_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    sweep_data.reorder(["ph1", "nScans", "t2"])
    fl.next("Raw - time")
    fl.image(
        sweep_data.C.mean("nScans")
        .setaxis("indirect", "#")
        .set_units("indirect", "scan #")
    )
    sweep_data.reorder('t2',first=False)
    sweep_data.ft("t2", shift=True)
    sweep_data.ft("ph1", unitary=True)
    fl.next("Raw - frequency")
    fl.image(
        sweep_data.C.mean("nScans")
        .setaxis("indirect", "#")
        .set_units("indirect", "scan #")
    )
else:
    if config_dict["nScans"] > 1:
        sweep_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    fl.next("Raw - time")
    fl.image(
        sweep_data.C.mean("nScans")
        .setaxis("indirect", "#")
        .set_units("indirect", "scan #")
    )
    sweep_data.reorder("t", first=False)
    sweep_data.ft("t", shift=True)
    fl.next("Raw - frequency")
    fl.image(
        sweep_data.C.mean("nScans")
        .setaxis("indirect", "#")
        .set_units("indirect", "scan #")
    )
sweep_data.name(config_dict["type"] + "_" + str(config_dict["field_counter"]))
sweep_data.set_prop("postproc_type", "field_sweep_v1")
target_directory = getDATADIR(exp_type="ODNP_NMR_comp/field_dependent")
filename_out = filename + ".h5"
nodename = sweep_data.name()
if os.path.exists(filename + ".h5"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        if nodename in fp.keys():
            print("this nodename already exists, so I will call it temp")
            sweep_data.name("temp")
            nodename = "temp"
    sweep_data.hdf5_write(f"{filename_out}", directory=target_directory)
else:
    try:
        sweep_data.hdf5_write(f"{filename_out}", directory=target_directory)
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
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(("Name of saved data", sweep_data.name()))
print(("Shape of saved data", ndshape(sweep_data)))
config_dict.write()
fl.show()
