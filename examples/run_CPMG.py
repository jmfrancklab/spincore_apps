"""
CPMG
====

This script will perform a standard CPMG experiment. 
In order to form a symmetric echo, a padding time is added before 
and after your tau through a series of delays. 
If you wish to keep the field as is without adjustment, follow
the 'py run_CPMG.py' command with 'stayput' (e.g. 'py run_CPMG.py stayput')
"""
from pylab import *
from pyspecdata import *
from numpy import *
import SpinCore_pp
from SpinCore_pp import prog_plen, get_integer_sampling_intervals
from SpinCore_pp.ppg import generic
import os, sys
from datetime import datetime
import h5py
from Instruments.XEPR_eth import xepr

# {{{ command-line option to leave the field untouched (if you set it once, why set it again)
adjust_field = True
if len(sys.argv) == 2 and sys.argv[1] == "stayput":
    adjust_field = False
# }}}
# {{{let computer set field
if adjust_field:
    print(
        "I'm assuming that you've tuned your probe to",
        config_dict["carrierFreq_MHz"],
        "since that's what's in your .ini file",
    )
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
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
(
    nPoints,
    config_dict["SW_kHz"],
    config_dict["echo_acq_ms"],
) = get_integer_sampling_intervals(
    config_dict["SW_kHz"], config_dict["echo_acq_ms"]
)
my_exp_type = "ODNP_NMR_comp/Echoes"
target_directory = getDATADIR(exp_type=my_exp_type)
assert os.path.exists(target_directory)
# }}}
# {{{create filename and save to config file
date = datetime.now().strftime("%y%m%d")
config_dict["type"] = "CPMG"
config_dict["date"] = date
config_dict["cpmg_counter"] += 1
filename = f"{config_dict['date']}_{config_dict['chemical']}_generic_{config_dict['type']}"
# }}}
# {{{set phase cycling
ph2 = r_[0, 1, 2, 3]
ph_diff = r_[0, 2]
ph1_cyc = array([(j + k) % 4 for k in ph2 for j in ph_diff])
ph2_cyc = array([(k + 1) % 4 for k in ph2 for j in ph_diff])
nPhaseSteps = len(ph2) * len(ph_diff)
# }}}
prog_p90_us = prog_plen(config_dict["p90_us"])
prog_p180_us = prog_plen(2 * config_dict["p90_us"])
# {{{ calculate symmetric tau by dividing 2tau by 2
# note that here the tau_us is defined as the evolution time from
# the start of excitation (*during the pulse*) through to the 
# start of the 180 pulse
marker_us = 1.0 #the marker takes 1 us
config_dict["tau_us"] = (
    2 * config_dict["deadtime_us"] + 1e3 * config_dict["echo_acq_ms"]
) / 2
assert (
    config_dict["tau_us"]
    > 2 * prog_p90_us / pi + marker_us + config_dict["deblank_us"]
)
assert config_dict["deadtime_us"] > config_dict["deblank_us"] + 2 * marker_us
print(
    "If you are measuring on a scope, the time from the start (or end) of one 180 pulse to the next should be %0.1f us"
    % (
        2 * config_dict["deadtime_us"]
        + 1e3 * config_dict["echo_acq_ms"]
        + prog_p180_us
    )
)
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps * config_dict["nEchoes"]
assert total_pts < 2**14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"
    % total_pts
)
# }}}
data = generic(
    ppg_list=[
        ("phase_reset", 1),
        ("delay_TTL", config_dict["deblank_us"]),
        ("pulse_TTL", prog_p90_us, "ph_cyc", ph1_cyc),
        (
            "delay",
            config_dict["tau_us"]
            - 2 * prog_p90_us / pi
            - marker_us
            - config_dict["deblank_us"],
        ),
# note that here the tau_us is defined as the evolution time from
# the start of excitation (*during the pulse*) through to the 
# start of the 180 pulse
        ("marker", "echo_label", config_dict["nEchoes"]),
        ("delay_TTL", config_dict["deblank_us"]),
        ("pulse_TTL", prog_p180_us, "ph_cyc", ph2_cyc),
        ("delay", config_dict["deadtime_us"]),
        ("acquire", config_dict["echo_acq_ms"]),
        (
            "delay",
            config_dict["deadtime_us"]
            - 2 * marker_us
            - config_dict["deblank_us"],
        ),
        ("jumpto", "echo_label"),
        # In the line above I assume this takes marker_us to execute
        # The way to be sure of this would be to capture on a scope and
        # measure from one 180 to the next (or actually several, since
        # this error would be cumulative
        ("delay", config_dict["repetition_us"]),
    ],
    nScans=config_dict["nScans"],
    indirect_idx=0,
    indirect_len=1,
    adcOffset=config_dict["adc_offset"],
    carrierFreq_MHz=config_dict["carrierFreq_MHz"],
    nPoints=nPoints,
    acq_time_ms=config_dict["echo_acq_ms"],
    SW_kHz=config_dict["SW_kHz"],
    ret_data=None,
)
## {{{ chunk and save data
data.set_prop("postproc_type", "spincore_diffph_SE_v1")
data.set_prop("coherence_pathway", {"ph_overall": -1, "ph1": +1})
data.set_prop("acq_params", config_dict.asdict())
nodename = config_dict["type"] + "_" + str(config_dict["cpmg_counter"])
data.name(nodename)
data.chunk(
    "t",
    ["ph2", "ph_diff", "nEcho", "t2"],
    [len(ph2), len(ph_diff), int(config_dict["nEchoes"]), -1],
)
data.setaxis("ph2", ph2 / 4)
data.setaxis("ph_diff", ph_diff / 4)
# }}}
filename_out = filename + ".h5"
if os.path.exists(f"{filename_out}"):
    print("this file already exists so we will add a node to it!")
    with h5py.File(
        os.path.normpath(os.path.join(target_directory, f"{filename_out}"))
    ) as fp:
        tempcounter = 1
        orig_nodename = nodename
        while nodename in fp.keys():
            nodename = "%s_temp_%d"%(orig_nodename,tempcounter)
            data.name(nodename)
            tempcounter += 1
    data.hdf5_write(f"{filename_out}", directory=target_directory)
print("\n*** FILE SAVED IN TARGET DIRECTORY ***\n")
print(
    "saved data to (node, file, exp_type):",
    data.name(),
    filename_out,
    my_exp_type,
)
config_dict.write()
