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
import pyspecProcScripts
import subprocess, os
import SpinCore_pp
from SpinCore_pp import get_integer_sampling_intervals
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
from Instruments.XEPR_eth import xepr
import h5py

my_exp_type = "ODNP_NMR_comp/Echoes"
target_directory = getDATADIR(exp_type=my_exp_type)
assert os.path.exists(target_directory)
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
(
    nPoints,
    config_dict["SW_kHz"],
    config_dict["acq_time_ms"],
) = get_integer_sampling_intervals(
    SW_kHz=config_dict["SW_kHz"],
    acq_time_ms=config_dict["acq_time_ms"],
)
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
# default phase cycling of run_spin_echo is to use a 4 step on the 90 pulse
# so this is here just for setting the chunked axis later and calculating the
# total points
ph1_cyc = r_[0, 1, 2, 3]
nPhaseSteps = 4
# }}}
print(
    "I'm assuming that you've tuned your probe to",
    config_dict["carrierFreq_MHz"],
    "since that's what's in your .ini file."
)
input("Hit enter if this is true")
# {{{ let computer set field
field_G = config_dict["carrierFreq_MHz"] / config_dict["gamma_eff_MHz_G"]
print(
    "Based on that, and the gamma_eff_MHz_G you have in your .ini file, I'm setting the field to %f"
    % field_G
)
with xepr() as x:
    assert field_G < 3700, "are you crazy??? field is too high!"
    assert field_G > 3300, "are you crazy?? field is too low!"
    field_G = x.set_field(field_G)
    print("field set to ", field_G)
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2**14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
# {{{ acquire echo
data = run_spin_echo(
    nScans=config_dict["nScans"],
    indirect_idx=0,
    indirect_len=1,
    ph1_cyc=ph1_cyc,
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    nEchoes=1,  # you should never be running a hahn echo with >1 echo
    p90_us=config_dict["p90_us"],
    amplitude=config_dict["amplitude"],
    repetition_us=config_dict["repetition_us"],
    tau_us=config_dict["tau_us"],
    SW_kHz=config_dict["SW_kHz"],
    ret_data=None,
)
# }}}
# {{{ chunk and save data
data.chunk(
    "t",
    ["ph1", "t2"],
    [len(ph1_cyc), -1],
)
data.setaxis("ph1", ph1_cyc / 4)
data.reorder(["ph1", "nScans", "t2"])
data.set_prop("postproc_type", "spincore_SE_v1")
data.set_prop("coherence_pathway", {"ph1": +1})
data.set_prop("acq_params", config_dict.asdict())
nodename = config_dict["type"] + "_" + str(config_dict["echo_counter"])
data.name(nodename)
filename_out = filename + ".h5"
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        while nodename in fp.keys():
            nodename = (
                config_dict["type"] + "_" + str(config_dict["echo_counter"])
            )
            data.name(nodename)
            config_dict["echo_counter"] += 1
data.hdf5_write(f"{filename_out}", directory=target_directory)
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(
    "Your *current* γ_eff (MHz/G) should be ",
    config_dict["gamma_eff_MHz_G"],
    " - (Δν*1e-6/",
    field_G,
    "), where Δν is your resonance offset",
)
print(
    "saved data to (node, file, exp_type):",
    data.name(),
    filename_out,
    my_exp_type,
)
config_dict.write()
# }}}
env = os.environ
subprocess.call("which python",shell=True)
subprocess.call((" ".join(["python",os.path.join(
    os.path.split(os.path.split(pyspecProcScripts.__file__)[0])[0],
    "examples", "proc_raw.py"),
    data.name(),filename_out, my_exp_type])),
    env=env)
