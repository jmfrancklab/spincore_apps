"""
Spin Echo
=========

To run this experiment, please open Xepr on the EPR computer, connect to
spectrometer, load the experiment 'set_field' and enable XEPR API. Then, in a
separate terminal, run the program XEPR_API_server.py, and wait for it to
tell you 'I am listening' - then, you should be able to run this program from
the NMR computer to set the field etc. 
"""

from pylab import *
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
from Instruments.XEPR_eth import xepr
import h5py

fl = figlist_var()
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
config_dict["SW_kHz"] = 75e6/round(75e6/config_dict["SW_kHz"]/1e3)/1e3
nPoints = int(config_dict["acq_time_ms"] * config_dict["SW_kHz"] + 0.5)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "echo"
config_dict["date"] = date
config_dict["echo_counter"] += 1
filename = (
    f"{config_dict['date']}_{config_dict['chemical']}_{config_dict['type']}"
)
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
# {{{let computer set field
print(
    "I'm assuming that you've tuned your probe to",
    config_dict["carrierFreq_MHz"],
    "since that's what's in your .ini file",
)
Field = config_dict["carrierFreq_MHz"] / config_dict["gamma_eff_MHz_G"]
print(
    "Based on that, and the gamma_eff_MHz_G you have in your .ini file, I'm setting the field to %f"
    % Field
)
with xepr() as x:
    assert Field < 3700, "are you crazy??? field is too high!"
    assert Field > 3300, "are you crazy?? field is too low!"
    Field = x.set_field(Field)
    print("field set to ", Field)
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2**14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
# {{{acquire echo
echo_data = run_spin_echo(
    nScans=config_dict["nScans"],
    indirect_idx=0,
    indirect_len=1,
    ph1_cyc=ph1_cyc,
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    nEchoes=config_dict["nEchoes"],
    p90_us=config_dict["p90_us"],
    repetition_us=config_dict["repetition_us"],
    tau_us=config_dict["tau_us"],
    SW_kHz=config_dict["SW_kHz"],
    ret_data=None,
)
# }}}
# {{{ chunk and save data
if phase_cycling:
    echo_data.chunk("t", ["ph1", "t2"], [len(ph1_cyc), -1])
    echo_data.setaxis("ph1", ph1_cyc / 4)
    if config_dict["nScans"] > 1:
        echo_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    echo_data.reorder(["ph1", "nScans", "t2"])
    echo_data.squeeze()
    echo_data.set_units("t2", "s")
    fl.next("Raw - time")
    fl.image(echo_data)
    echo_data.reorder("t2", first=False)
    for_plot = echo_data.C
    for_plot.ft("t2", shift=True)
    for_plot.ft(["ph1"], unitary=True)
    fl.next("FTed data")
    fl.image(for_plot)
else:
    if config_dict["nScans"] > 1:
        echo_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
    echo_data.rename("t", "t2")
    fl.next("Raw - time")
    fl.image(echo_data)
    echo_data.reorder("t2", first=False)
    for_plot = echo_data.C
    for_plot.ft("t2", shift=True)
    fl.next("FTed data")
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
print(("Name of saved data",echo_data.name()))
print(("Shape of saved data",ndshape(echo_data)))
config_dict.write()
if phase_cycling:
    echo_data.ft('t2',shift=True)
    fl.next('image - ft')
    fl.image(echo_data)
    fl.next('image - ft, coherence')
    echo_data.ft(['ph1'])
    fl.image(echo_data)
    fl.next('data plot')
    if 'nScans' in echo_data.dimlabels:
        data_slice = echo_data['ph1',1].mean('nScans')
    else:
        data_slice = echo_data['ph1',1]
    fl.plot(data_slice, alpha=0.5)
    fl.plot(data_slice.imag, alpha=0.5)
    fl.plot(abs(data_slice), color='k', alpha=0.5)
else:
    fl.next('raw data')
    fl.plot(echo_data)
    echo_data.ft('t',shift=True)
    fl.next('ft')
    if 'nScans' in echo_data.dimlabels:
        data_slice = echo_data.mean('nScans')
    else:
        data_slice = echo_data['ph1',1]
    fl.plot(data_slice.real)
    fl.plot(data_slice.imag)
    fl.plot(abs(data_slice),color='k',alpha=0.5)
fl.show()
