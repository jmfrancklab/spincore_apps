"""
Nutation
========

A standard echo where the 90 time is varied so 
that we are able to see when the signal rotates through 90 to 
180 degrees.
"""
from pyspecdata import *
import os
import SpinCore_pp
from SpinCore_pp import get_integer_sampling_intervals, save_data
from Instruments.XEPR_eth import xepr
from SpinCore_pp.ppg import run_spin_echo
from datetime import datetime
from numpy import linspace, arange

my_exp_type = "ODNP_NMR_comp/nutation"
assert os.path.exists(getDATADIR(exp_type=my_exp_type))
p90_range_us = linspace(1.0, 10.0, 20, endpoint=False)
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
(
    nPoints,
    config_dict["SW_kHz"],
    config_dict["acq_time_ms"],
) = get_integer_sampling_intervals(
    config_dict["SW_kHz"], config_dict["acq_time_ms"]
    )
# }}}
# {{{add file saving parameters to config dict
config_dict["type"] = "nutation"
config_dict["date"] = datetime.now().strftime("%y%m%d")
config_dict["echo_counter"] += 1
# }}}
# {{{set phase cycling
ph1_cyc = r_[0, 1, 2, 3]
nPhaseSteps = 4
# }}}
# {{{let computer set field
input(
    "I'm assuming that you've tuned your probe to:",
    config_dict["carrierFreq_MHz"],
    "since that's what's in your .ini file.  Hit enter if this is true",
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
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2**14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384\nyou could try reducing the acq_time_ms to %f"
    % (total_pts, config_dict["acq_time_ms"] * 16384 / total_pts)
)
# }}}
nutation_data = None
for idx, p90_us in enumerate(p90_range_us):
    # Just loop over the 90 times and set the indirect axis at the end
    # just like how we perform and save IR data
    nutation_data = run_spin_echo(
        deadtime_us=config_dict["deadtime_us"],
        nScans=config_dict["nScans"],
        indirect_idx=idx,
        indirect_len=len(p90_range_us),
        ph1_cyc=ph1_cyc,
        amplitude=config_dict["amplitude"],
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        nEchoes=config_dict["nEchoes"],
        p90_us=p90_us,
        repetition_us=config_dict["repetition_us"],
        tau_us=config_dict["tau_us"],
        SW_kHz=config_dict["SW_kHz"],
        ret_data=nutation_data,
    )
nutation_data.setaxis("indirect", p90_range_us * 1e-6).set_units(
    "indirect", "s"
    )
# {{{ chunk and save data
nutation_data.chunk("t", ["ph1", "t2"], [4, -1])
nutation_data.setaxis("ph1", ph1_cyc / 4)
if config_dict["nScans"] > 1:
    nutation_data.setaxis("nScans", r_[0 : config_dict["nScans"]])
nutation_data.reorder(["ph1", "nScans", "t2"])
nutation_data.set_units("t2", "s")
nutation_data.set_prop("postproc_type", "spincore_nutation_v4")
nutation_data.set_prop("coherence_pathway", {"ph1": +1})
nutation_data.set_prop("acq_params", config_dict.asdict())
config_dict = save_data(data, my_exp_type, config_dict, "echo")
config_dict.write()
