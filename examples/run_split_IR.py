"""
Stimulated Echo Inversion Recovery - Split IR
=============================================
The initial 180 pulse of a typical inversion recovery experiment is split into
two closely spaced 90 pulses instead.  We can then track the 2 different
coherence pathways involved in the IR process: 1) the "phase memory" pathway
and 2) the "relaxed" pathway. The first of the two is affected by the phase of
the first two pulses whereas the signal from the second pathway comes from the
subensemble that has relaxed back to equilibrium.
If you wish to keep the field as is without adjustment, follow the 'py
run_split_IR.py' command with 'stayput' (e.g. 'py run_split_IR.py stayput')
"""
from pylab import *
from pyspecdata import *
import os, sys
from numpy import *
import SpinCore_pp
from SpinCore_pp import prog_plen, get_integer_sampling_intervals, save_data
from SpinCore_pp.ppg import generic
from datetime import datetime
from Instruments.XEPR_eth import xepr

my_exp_type = "ODNP_NMR_comp/IR"
assert os.path.exists(getDATADIR(exp_type=my_exp_type))
# {{{importing acquisition parameters
config_dict = SpinCore_pp.configuration("active.ini")
(
    nPoints,
    config_dict["SW_kHz"],
    config_dict["acq_time_ms"],
) = get_integer_sampling_intervals(
    SW_kHz=config_dict["SW_kHz"],
    time_per_segment_ms=config_dict["acq_time_ms"],
)
# }}}
# {{{add file saving parameters to config dict
config_dict["type"] = "IR"
config_dict["date"] = datetime.now().strftime("%y%m%d")
config_dict["IR_counter"] += 1
# }}}
# {{{ command-line option to leave the field untouched (if you set it once, why set it again)
adjust_field = True
if len(sys.argv) == 2 and sys.argv[1] == "stayput":
    adjust_field = False
# }}}
input(
    "I'm assuming that you've tuned your probe to %f since that's what's
    in your .ini file. Hit enter if this is true" %
    config_dict["carrierFreq_MHz"]
)
# {{{ let computer set field
if adjust_field:
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
# {{{set phase cycling
ph1_cyc = r_[0, 1, 2, 3]
ph3_cyc = r_[0, 1, 2, 3]
nPhaseSteps = len(ph1_cyc)*len(ph3_cyc)
# }}}
# {{{ calibrate pulse lengths
# NOTE: This is done inside the run_spin_echo rather than in the example
# but to keep the generic function more robust we do it outside of the ppg
prog_p90_us = prog_plen(config_dict["p90_us"])
prog_p180_us = prog_plen(2 * config_dict["p90_us"])
# }}}
# {{{ make vd list
vd_kwargs = {
        j: config_dict[j]
        for j in ["krho_cold", "krho_hot", "T1water_cold", "T1water_hot"]
        if j in config_dict.keys()
}
vd_list_us = (
        SpinCore_pp.vdlist_from_relaxivities(config_dict["concentration"], **vd_kwargs)
        *1e6
)
# }}}
# {{{check total points
total_pts = nPoints * nPhaseSteps
assert total_pts < 2**14, (
    "You are trying to acquire %d points (too many points) -- either change SW or acq time so nPoints x nPhaseSteps is less than 16384"
    % total_pts
)
# }}}
bn_90_delay_us = 3 #3 us delay between two 90 pulses
# {{{ acquire split IR
vd_data = None
for vd_idx, vd in enumerate(vd_list_us):
    vd_data = generic(
        ppg_list=[
            ("phase_reset", 1),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", prog_p90_us, "ph1", ph1_cyc),
            ("delay", bn_90_delay_us),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", prog_p90_us, 0),
            ("delay", vd),
            ("delay_TTL", config_dict["deblank_us"]),
            ("pulse_TTL", prog_p90_us, "ph3", ph3_cyc),
            ("delay", config_dict["deadtime_us"]),
            ("acquire", config_dict["acq_time_us"]),
            ("delay", config_dict["repetition_us"]),
        ],
        nScans=config_dict["nScans"],
        indirect_idx=vd_idx,
        indirect_len=len(vd_list_us),
        adcOffset=config_dict["adc_offset"],
        carrierFreq_MHz=config_dict["carrierFreq_MHz"],
        nPoints=nPoints,
        time_per_segment_ms=config_dict["acq_time_ms"],
        SW_kHz=config_dict["SW_kHz"],
        ret_data=vd_data,
    )
# }}}
# {{{ chunk and save data
data.chunk(
    "t",
    ["ph3", "ph1", "t2"],
    [len(ph3_cyc), len(ph1_cyc), -1],
)
data.setaxis("ph3", ph3_cyc / 4).setaxis("ph3",ph3_cyc / 4)
data.set_prop("postproc_type", "spincore_split_IR_v1")
data.set_prop("coherence_pathway", {"ph1": 0, "ph3": -1}) #relaxed pathway
data.set_prop("acq_params", config_dict.asdict())
config_dict = save_data(data, my_exp_type, config_dict, "IR")
config_dict.write()
# }}}

